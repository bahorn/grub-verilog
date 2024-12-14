module counter(clk, count);
  input wire clk;
  output reg [7:0] count;

  always @(posedge clk) begin
    if (count == 8'hff) count <= 8'h0; // rollover to 0 when count reaches max value
    else count <= count + 1;
  end

endmodule
