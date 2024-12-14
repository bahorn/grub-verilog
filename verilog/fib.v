/* slightly modified demo code from oss-cad-suite */
module fib (
	input clk, pause, start,
	input [3:0] n,
	output reg busy, done,
	output reg [9:0] f
);
	reg [3:0] count;
	reg [9:0] q;

	initial begin
		done = 0;
		busy = 0;
	end

	always @(posedge clk) begin
		done <= 0;
		if (!pause) begin
			if (!busy) begin
				if (start)
					busy <= 1;
				count <= 0;
				q <= 1;
				f <= 0;
			end else begin
				q <= f;
				f <= f + q;
				count <= count + 1;
				if (count == n) begin
					busy <= 0;
					done <= 1;
				end
			end
		end
	end
endmodule
