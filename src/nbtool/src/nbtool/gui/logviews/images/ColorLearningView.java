package nbtool.gui.logviews.images;

import java.awt.Dimension;
import java.awt.Graphics;
import java.awt.event.ComponentAdapter;
import java.awt.event.ComponentEvent;
import java.awt.event.MouseEvent;
import java.awt.event.MouseListener;
import java.awt.event.MouseMotionListener;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.util.HashMap;
import java.util.Map;

import nbtool.images.Y8image;
import nbtool.images.UV8image;
import nbtool.images.Y16image;

import nbtool.data.Log;
import nbtool.gui.logviews.misc.ViewParent;
import nbtool.util.Utility;

import nbtool.io.CommonIO.IOFirstResponder;
import nbtool.io.CommonIO.IOInstance;
import nbtool.io.CrossIO;
import nbtool.io.CrossIO.CrossCall;
import nbtool.io.CrossIO.CrossFunc;
import nbtool.io.CrossIO.CrossInstance;

public class ColorLearningView extends ViewParent implements MouseMotionListener, IOFirstResponder {
	BufferedImage u_img;
	BufferedImage v_img;
	BufferedImage y_img;
	BufferedImage alt_img;
	BufferedImage original_image;
	private String label = null;
	
	public void paintComponent(Graphics g) {
		super.paintComponent(g);
        
		if (original_image != null)
			g.drawImage(original_image, 0, 0, null);
		if (u_img != null)
			g.drawImage(u_img, 0, original_image.getHeight() + 15, null);
		if (v_img != null)
			g.drawImage(v_img, u_img.getWidth() + 10, original_image.getHeight() + 15, null);
		if (y_img != null)
			g.drawImage(y_img, 2 * u_img.getWidth() + 20, original_image.getHeight() + 15, null);
		if (alt_img != null) {
			g.drawImage(alt_img, 0, u_img.getHeight() + original_image.getHeight() + 30, null);
        } 
		if (label != null)
			g.drawString(label, 10, original_image.getHeight() + u_img.getHeight() + 25);
    }
	
	public void setLog(Log newlog) {		
		// this.u_img = Utility.biFromLog(newlog);
		this.original_image = Utility.biFromLog(newlog);
		
		CrossInstance inst = CrossIO.instanceByIndex(0);
		if (inst == null)
			return;

		CrossFunc func = inst.functionWithName("ColorLearnTest");
		if (func == null)
			return;
		
		CrossCall call = new CrossCall(this, func, this.log);
		inst.tryAddCall(call);

		repaint();
	}
	
	public ColorLearningView() {
		super();
		setLayout(null);
		this.addMouseMotionListener(this);
	}

	@Override
	public void ioFinished(IOInstance instance) {}

	@Override
	public void ioReceived(IOInstance inst, int ret, Log... out) {
		if (out.length > 0) {
            UV8image u8 = new UV8image(320, 240, out[0].bytes, true);
            this.u_img = u8.toBufferedImage();

            UV8image v8 = new UV8image(320, 240, out[1].bytes, false);
            this.v_img = v8.toBufferedImage();

            Y16image yImg = new Y16image(320, 240, out[2].bytes);
            this.y_img = yImg.toBufferedImage();

            UV8image altImg = new UV8image(320, 240, out[3].bytes, true);
            this.alt_img = altImg.toBufferedImage();

        	// get u histogram vals
	        HashMap<Integer, Integer> u_line_vals = new HashMap<Integer, Integer>();
	        byte[] uBytes = out[4].bytes;
	        int numPairs = uBytes.length / (2 * 4);
        	System.out.println("[HISTOGRAM] uBytes: " + uBytes.length);
	        try {
	            DataInputStream dis = new DataInputStream(new ByteArrayInputStream(uBytes));

	            for (int i = 0; i < numPairs; i++) {
	            	Integer u_val_key = new Integer(dis.readInt());
	            	Integer u_val_val = new Integer(dis.readInt());
	            	u_line_vals.put(u_val_key, u_val_val);
	            }
	        } catch (Exception e) {
	            e.printStackTrace();
	        }

        	System.out.println("[HISTOGRAM] BEFORE PRINTS");
	        // print u histogram vals
	        for (Integer name : u_line_vals.keySet()){
	            String key = name.toString();
	            String value = u_line_vals.get(name).toString();  
	            System.out.println(key + " : " + value);  
			} 
        	System.out.println("[HISTOGRAM] AFTER PRINTS");



	    }
        else {
			System.out.println("ERROR no output received");
        }
		// this.img = Utility.biFromLog(out[0]);
		repaint();
	}

	@Override
	public boolean ioMayRespondOnCenterThread(IOInstance inst) {
		return false;
	}

	@Override
	public void mouseDragged(MouseEvent e) {}

	@Override
	public void mouseMoved(MouseEvent e) {
		if (original_image == null || log == null)
			return;
		
		int col = e.getX();
		int row = e.getY();
		
		if (col < 0 || row < 0 || col >= original_image.getWidth() || row >= original_image.getHeight())
			return;
		
		boolean first = (col & 1) == 0;
		int cbase = (col & ~1);
		int i = (row * original_image.getWidth() * 2) + (cbase * 2);
		
		int y = log.data()[first ? i : i + 2] & 0xff;
		int u = log.data()[i + 1] & 0xff;
		int v = log.data()[i + 3] & 0xff;
		label = String.format("(%d,%d): y=%d u=%d v=%d", col, row, y, u, v);
		repaint();
	}
	
}
