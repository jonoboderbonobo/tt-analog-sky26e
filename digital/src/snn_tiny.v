// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 Jonas Boerschmann
//
// snn_tiny: a small event-driven spiking network with the arithmetic of the tinyODIN model in snn_gym
// (snn/tinyodin.py, lif_syn and lif_leak; reference RTL C. Frenkel, tinyODIN, Solderpad SHL-2.1):
//   12-bit signed state, 4-bit signed weights, saturating add, spike when state >= thr, reset to 0,
//   time-reference event moves every state toward zero by `leak` (clamped at 0).
// Differences from tinyODIN, all for area: NN neurons only, rows 0..NN-1 are the recurrent rows (a spike of
// neuron i is event row i), rows NN..NN+NI-1 are input lines; weights, thr and leak sit in flip-flops and are
// written through the write port; thr and leak are shared by all neurons; no neuron disable, no AER, no learning.
// Events are processed one neuron per clock. Internal spike events go into a FIFO of DEPTH entries; the event
// being processed stays in the FIFO, and spikes that find it full are dropped (as in the model).
`default_nettype none

module snn_tiny #(
    parameter NN    = 8,           // neurons
    parameter NI    = 4,           // input lines
    parameter DEPTH = 8            // FIFO entries
) (
    input  wire                      clk,
    input  wire                      rst_n,

    // write port: one write per clock
    input  wire                      w_we,       // weight write
    input  wire [RW-1:0]             w_row,
    input  wire [JW-1:0]             w_col,
    input  wire [3:0]                w_data,
    input  wire                      thr_we,
    input  wire [11:0]               thr_data,
    input  wire                      leak_we,
    input  wire [6:0]                leak_data,

    // events
    input  wire                      in_valid,   // external input line event (pushed into the FIFO)
    input  wire [IW-1:0]             in_line,    // input line 0..NI-1, row NN+in_line
    input  wire                      tref,       // time reference event: leak all neurons (latched while busy)

    output wire                      busy,       // events pending or being processed
    output wire [NN-1:0]             spk_last,   // neurons that spiked at the last event
    output wire                      spk_pulse,  // one clock: a neuron spiked (spk_idx valid)
    output wire [JW-1:0]             spk_idx,
    output wire [12*NN-1:0]          state_flat  // all states, for tests and readback
);
    localparam NR = NN + NI;
    localparam RW = (NR  <= 2) ? 1 : $clog2(NR);
    localparam JW = (NN  <= 2) ? 1 : $clog2(NN);
    localparam IW = (NI  <= 2) ? 1 : $clog2(NI);
    localparam PW = (DEPTH <= 2) ? 1 : $clog2(DEPTH);
    localparam CW = $clog2(DEPTH + 1);
    localparam [RW-1:0] NN_R = NN;

    // ---- memories ------------------------------------------------------------------------------------------
    reg [4*NR*NN-1:0] wmem;
    reg [11:0]        thr;
    reg [6:0]         leak;
    reg [12*NN-1:0]   st;
    assign state_flat = st;

    always @(posedge clk) begin
        // wmem has no reset (area): the host writes every weight after power-up
        if (w_we) wmem[(w_row*NN + w_col)*4 +: 4] <= w_data;
        if (!rst_n) begin
            thr  <= 12'd0;
            leak <= 7'd0;
        end else begin
            if (thr_we)  thr  <= thr_data;
            if (leak_we) leak <= leak_data;
        end
    end

    // ---- FIFO of pre-synaptic rows ---------------------------------------------------------------------------
    reg [RW-1:0] fifo [0:DEPTH-1];
    reg [PW-1:0] rd, wr;
    reg [CW-1:0] cnt;

    // ---- control -------------------------------------------------------------------------------------------
    localparam S_IDLE = 2'd0, S_SYN = 2'd1, S_TREF = 2'd2;
    reg [1:0]    fsm;
    reg [JW-1:0] j;
    reg          tref_pend;
    reg [NN-1:0] spk_r;
    reg          pulse_r;
    reg [JW-1:0] idx_r;

    assign busy      = (fsm != S_IDLE) || (cnt != 0) || tref_pend;
    assign spk_last  = spk_r;
    assign spk_pulse = pulse_r;
    assign spk_idx   = idx_r;

    wire [RW-1:0] cur   = fifo[rd];
    wire [RW-1:0] j_row = j;                                                   // zero-extended
    wire last_j = (j == NN - 1);

    // ---- one neuron update --------------------------------------------------------------------------------
    wire signed [11:0] s_old  = st[j*12 +: 12];
    wire signed [3:0]  w_cur  = wmem[(cur*NN + j)*4 +: 4];
    wire signed [12:0] sum    = s_old + w_cur;                                  // 13 bit: no overflow
    wire signed [11:0] s_syn  = (sum > 13'sd2047) ? 12'sd2047 : (sum < -13'sd2048) ? -12'sd2048 : sum[11:0];
    wire signed [12:0] leak_x = {6'b0, leak};
    wire signed [12:0] s_up   = s_old + leak_x;                                 // negative state: toward 0
    wire signed [12:0] s_dn   = s_old - leak_x;                                 // positive state: toward 0
    wire signed [11:0] s_lk   = (s_old < 0) ? ((s_up > 13'sd0) ? 12'sd0 : s_up[11:0])
                                            : ((s_dn < 13'sd0) ? 12'sd0 : s_dn[11:0]);
    wire signed [11:0] s_new  = (fsm == S_TREF) ? s_lk : s_syn;
    wire               fire   = ($signed({1'b0, thr}) <= $signed({s_new[11], s_new}));  // s_new >= thr, thr >= 0
    wire signed [11:0] s_next = fire ? 12'sd0 : s_new;
    wire               sweeping = (fsm == S_SYN) || (fsm == S_TREF);
    wire               int_push = sweeping && fire && (cnt < DEPTH);            // internal spikes: dropped when full
    wire               ext_push = in_valid && !int_push && (cnt < DEPTH);       // see note below
    wire               pop      = (fsm == S_SYN) && last_j;

    always @(posedge clk) begin
        if (!rst_n) begin
            fsm <= S_IDLE; j <= 0; rd <= 0; wr <= 0; cnt <= 0;
            tref_pend <= 1'b0; spk_r <= {NN{1'b0}}; pulse_r <= 1'b0; idx_r <= 0;
            st <= {12*NN{1'b0}};
        end else begin
            pulse_r <= 1'b0;
            if (tref) tref_pend <= 1'b1;

            case (fsm)
                S_IDLE: begin
                    j <= 0;
                    if (tref_pend)      begin fsm <= S_TREF; tref_pend <= 1'b0; spk_r <= {NN{1'b0}}; end
                    else if (cnt != 0)  begin fsm <= S_SYN;  spk_r <= {NN{1'b0}}; end
                end
                S_SYN, S_TREF: begin
                    st[j*12 +: 12] <= s_next;
                    if (fire) begin spk_r[j] <= 1'b1; pulse_r <= 1'b1; idx_r <= j; end
                    j <= last_j ? {JW{1'b0}} : j + 1'b1;
                    if (last_j) fsm <= S_IDLE;
                end
                default: fsm <= S_IDLE;
            endcase

            // FIFO: one push per clock. The host must not send an input event while a sweep can push
            // (it waits for busy = 0, as the model's quiet host does), so in_valid and an internal push do not collide.
            if (int_push) begin
                fifo[wr] <= j_row;
                wr <= (wr == DEPTH - 1) ? {PW{1'b0}} : wr + 1'b1;
            end else if (ext_push) begin
                fifo[wr] <= NN_R + in_line;
                wr <= (wr == DEPTH - 1) ? {PW{1'b0}} : wr + 1'b1;
            end
            if (pop) rd <= (rd == DEPTH - 1) ? {PW{1'b0}} : rd + 1'b1;
            cnt <= cnt + ((int_push || ext_push) ? 1 : 0) - (pop ? 1 : 0);
        end
    end
endmodule
`default_nettype wire
