package nbtool.images;

import java.awt.Color;
import java.awt.image.BufferedImage;

public class UV8image extends ImageParent {

	private boolean u;

	public int pixelSize() {return 1;}
	public UV8image(int w, int h, byte[] d, boolean _u) {
		super(w, h, d);
		u = _u;
		// TODO Auto-generated constructor stub
	}

	@Override
	public BufferedImage toBufferedImage() {
		BufferedImage ret = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
		for (int r = 0; r < height; ++r) {
			for (int c = 0; c < width; ++c) {
				
				byte color_byte = (data[r * width + c]);// & 0xFF;
				byte none = 127;		
				// Color color = new Color(y, y, y);
				if (u) {
				ret.setRGB(c, r, yuv444ToARGB888Pixel(color_byte, color_byte, color_byte));
				}
				else {
					ret.setRGB(c, r, yuv444ToARGB888Pixel(none, none, color_byte));
				}
			}
		}
		return ret;
	}

	@Override
	public String encoding() {
		return "[8U]";
	}

	public static int clamp(int val, int low, int high) {
		return Math.max(low, Math.min(high, val));
	}

	public static int yuv444ToARGB888Pixel(byte y, byte u, byte v) {
		int c = (int)(y & 0xFF) - 16;
		int d = (int)(u & 0xFF) - 128;
		int e = (int)(v & 0xFF) - 128;
		
		int r2 = clamp((298*c + 409*e + 128) >> 8, 0, 255);
		int g2 = clamp((298*c - 100*d - 208*e + 128) >> 8, 0, 255);
		int b2 = clamp((298*c + 516*d + 128) >> 8, 0, 255);
		
		return (255 << 24) + (r2 << 16) + (g2 << 8) + (b2);
	}

}
