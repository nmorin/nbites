package nbtool.images;

import java.awt.Color;
import java.awt.image.BufferedImage;

public class UV8image extends ImageParent {

	private boolean u;
	private boolean field_img;

	public int pixelSize() {return 1;}
	public UV8image(int w, int h, byte[] d, boolean _u, boolean _field_img) {
		super(w, h, d);
		u = _u;
		field_img = _field_img;
		// TODO Auto-generated constructor stub
	}

	@Override
	public BufferedImage toBufferedImage() {
		boolean colored_img = true;
		BufferedImage ret;
		if (colored_img)
			ret = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
		else 
			ret = new BufferedImage(width, height, BufferedImage.TYPE_BYTE_GRAY);
		
		for (int r = 0; r < height; ++r) {
			for (int c = 0; c < width; ++c) {
				
				byte color_byte = (data[r * width + c]);// & 0xFF;
				byte none = 127;		
				// Color color = new Color(y, y, y);
				if (color_byte == (byte)0) {
					// Color color = new Color(val, val, val);
					if (field_img) 
						ret.setRGB(c, r, (Color.green).getRGB());
					else
						ret.setRGB(c, r, (Color.white).getRGB());
				}
				// if (colored_img) {
				// 	if (u)	
				// 		ret.setRGB(c, r, yuv444ToARGB888Pixel(none, color_byte, none));
				// 	else
				// 		ret.setRGB(c, r, yuv444ToARGB888Pixel(none, none, color_byte));
				// }
				else {
					int val = color_byte & 0xFF;
					Color color = new Color(val, val, val);
					ret.setRGB(c, r, color.getRGB());
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
