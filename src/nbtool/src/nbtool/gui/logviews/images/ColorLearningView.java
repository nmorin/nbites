package nbtool.gui.logviews.images;

import java.awt.Dimension;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.geom.Rectangle2D;
import java.awt.geom.AffineTransform;
import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Font;
import java.awt.Dimension;
import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import java.awt.image.BufferedImage;

import javax.swing.JSlider;
import javax.swing.JTextField;
import javax.swing.JButton;
import javax.swing.event.*;

import java.io.ByteArrayInputStream;
import java.io.DataInputStream;

import java.util.HashMap;
import java.util.Map;
import java.util.TreeMap;
import java.lang.Math;

import nbtool.images.Y8image;
import nbtool.images.UV8image;
import nbtool.images.Y16image;

import nbtool.data.Log;
import nbtool.data.SExpr;
import nbtool.gui.logviews.misc.ViewParent;
import nbtool.util.Utility;

import nbtool.io.CommonIO.IOFirstResponder;
import nbtool.io.CommonIO.IOInstance;
import nbtool.io.CrossIO;
import nbtool.io.CrossIO.CrossCall;
import nbtool.io.CrossIO.CrossFunc;
import nbtool.io.CrossIO.CrossInstance;

public class ColorLearningView extends ViewParent implements MouseMotionListener, IOFirstResponder {
	// output images and original image
	BufferedImage u_img;
	BufferedImage v_img;
	BufferedImage y_img;
	BufferedImage green_img;
	BufferedImage alt_img;
	BufferedImage original_image;

	TreeMap<Integer, Integer> u_line_vals;
	TreeMap<Integer, Integer> u_all_vals;

    private JSlider fieldThreshSlider;
    private JTextField uTextField;
    private JButton repaintButton;

	// private String label = null;
	int MIN_BAR_WIDTH = 5;

	int calcMax(TreeMap<Integer, Integer> map) {
		int curr_max = -1;
		int key_max = -1;
		for (Integer key : map.keySet()) {
			if (map.get(key) > curr_max) {
				curr_max = map.get(key);
				key_max = key;
			}
		}
		return key_max;
	}

	public void drawHist(Graphics g, TreeMap<Integer, Integer> vals_map, int xBegin, int yBegin, int w, int h, String title) {

		if (vals_map != null) {
            int xOffset = xBegin;
            int yOffset = yBegin;
            int width = w;
            int height = h;

            Graphics2D g2d = (Graphics2D) g.create();
            g2d.setColor(Color.DARK_GRAY);
            g2d.drawRect(xOffset, yOffset, width, height);
            int barWidth = Math.max(MIN_BAR_WIDTH, (int) Math.floor((float) width
                    / (float) vals_map.size()));

            int maxValue = 0;
            for (Integer key : vals_map.keySet()) {
                int value = vals_map.get(key);
                maxValue = Math.max(maxValue, value);
            }
            int xPos = xOffset;


            Font titleFont = new Font(null, Font.BOLD, 10);
            g2d.setFont(titleFont); 
            g2d.drawString(title, xOffset + 15, yOffset + 15);
            int mapMax = calcMax(vals_map);
            String maxInfo = "Max: " + mapMax;
            g2d.drawString(maxInfo, xOffset + 25, yOffset + 25);


            int labelCount = 0;
            for (Integer key : vals_map.keySet()) {
                int value = vals_map.get(key);
                int barHeight = Math.round(((float) value / (float) maxValue) * height);
                g2d.setColor(new Color(key, key, key));
                int yPos = height + yOffset - barHeight;
                Rectangle2D bar = new Rectangle2D.Float(xPos, yPos, barWidth, barHeight);
                g2d.fill(bar);
                g2d.setColor(Color.DARK_GRAY);
                g2d.draw(bar);
                xPos += barWidth;

                if (labelCount < 2) {
                	labelCount++;
                	continue;
                }
                labelCount = 0;
                String value_label = "" + value;
                Font font = new Font(null, Font.PLAIN, 10);
                g2d.setFont(font); 
                AffineTransform affTran = new AffineTransform(); // g2d.getTransform();
                affTran.rotate(Math.toRadians(90), 0, 0);
				Font rotatedFont = font.deriveFont(affTran);
				g2d.setFont(rotatedFont);
                g2d.drawString(key.toString(), xPos - barWidth, yOffset + height + 10);
            }
            g2d.dispose();
        }


	}
	
	public void paintComponent(Graphics g) {
		super.paintComponent(g);
		int width = 0, height = 0;
        
		if (original_image != null) {
			width = original_image.getWidth() / 2;
			height = original_image.getHeight() / 2;
			g.drawImage(original_image, 0, 0, width, height, null);
		}
		if (u_img != null)
			g.drawImage(u_img, width + 5, 0, null);
		if (v_img != null)
			g.drawImage(v_img, width + 5, u_img.getHeight() + 5, null);
		if (y_img != null)
			g.drawImage(y_img, width + 5, 2*height + 10, null);
		if (alt_img != null)
			g.drawImage(alt_img, 0, height + 5, null);
		if (green_img != null)
			g.drawImage(green_img, 0, 2*height + 10, null);

		drawHist(g, u_line_vals, 2*width + 10, 5, 450, 200, "u_line_vals");
		drawHist(g, u_all_vals, 2*width + 10, height, 450, 200, "u_all_vals");

		// u threshold slider
		int sliderX = 5; 
		int sliderY = 3*height + 20;
		int sliderHeight = 15;
		fieldThreshSlider.setBounds(sliderX, sliderY, width, sliderHeight);
		g.drawString("width of u threshold for fieldcolor", sliderX, sliderY + 25);
		g.drawString("Current value: " + fieldThreshSlider.getValue(), sliderX, sliderY + 40);

		// draw u initial value text field
		g.drawString("u max: ", sliderX, sliderY + 55);
		uTextField.setBounds(sliderX, sliderY + 60, 50, 30);

		// draw repaint button
		repaintButton.setBounds(sliderX + 50, sliderY + 50, 100, 30);


    }
	
	public void setLog(Log newlog) {		
		this.original_image = Utility.biFromLog(newlog);
		callNBFunc();
	}

	public void callNBFunc() {
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

	public void adjustParams() {
		int uFieldVal = 0;
		if (!uTextField.getText().equals("")) 
			uFieldVal = Integer.parseInt(uTextField.getText());

		SExpr newFieldParams = SExpr.newList(
			SExpr.newKeyValue("uThreshold", fieldThreshSlider.getValue()),
			SExpr.newKeyValue("uFieldVal", uFieldVal)
		);

		SExpr oldFieldParams = this.log.tree().find("fieldParams");
		if (oldFieldParams.exists()) {
            oldFieldParams.setList( SExpr.atom("fieldParams"), newFieldParams); 
		} else {
            this.log.tree().append(SExpr.pair("fieldParams", newFieldParams));
        }

		callNBFunc();
	}
	
	public ColorLearningView() {
		super();
		setLayout(null);
		this.addMouseMotionListener(this);

		ChangeListener slide = new ChangeListener(){
	        public void stateChanged(ChangeEvent e) {
	            adjustParams();
	        }
	    };
	    
		fieldThreshSlider = new JSlider(JSlider.HORIZONTAL, 0, 25, 3);
		fieldThreshSlider.addChangeListener(slide);
		add(fieldThreshSlider);

		uTextField = new JTextField(3);
		repaintButton = new JButton("Repaint");
        repaintButton.addActionListener(new ActionListener() {
        public void actionPerformed(ActionEvent e) { 
        	adjustParams();      
        }});

        add(uTextField);
        add(repaintButton);
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

            // Line histogram data:
        	// Get u histogram vals -- lines
	        u_line_vals = new TreeMap<Integer, Integer>();
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

	        // Get v histogram vals -- lines
			HashMap<Integer, Integer> v_line_vals = new HashMap<Integer, Integer>();
	        byte[] vBytes = out[5].bytes;
	        numPairs = vBytes.length / (2 * 4);
        	System.out.println("[HISTOGRAM] vBytes: " + vBytes.length);
	        try {
	            DataInputStream dis = new DataInputStream(new ByteArrayInputStream(vBytes));
	            for (int i = 0; i < numPairs; i++) {
	            	Integer v_val_key = new Integer(dis.readInt());
	            	Integer v_val_val = new Integer(dis.readInt());
	            	v_line_vals.put(v_val_key, v_val_val);
	            }
	        } catch (Exception e) {
	            e.printStackTrace();
	        }	        

	        // Get y histogram vals -- lines
			HashMap<Integer, Integer> y_line_vals = new HashMap<Integer, Integer>();
	        byte[] yBytes = out[6].bytes;
	        numPairs = yBytes.length / (2 * 4);
        	System.out.println("[HISTOGRAM] yBytes: " + yBytes.length);
	        try {
	            DataInputStream dis = new DataInputStream(new ByteArrayInputStream(yBytes));
	            for (int i = 0; i < numPairs; i++) {
	            	Integer y_val_key = new Integer(dis.readInt());
	            	Integer y_val_val = new Integer(dis.readInt());
	            	y_line_vals.put(y_val_key, y_val_val);
	            }
	        } catch (Exception e) {
	            e.printStackTrace();
	        }

	        // Get yuv histogram vals
			// HashMap<Integer, Integer> yuv_line_vals = new HashMap<Integer, Integer>();
	  //       byte[] yuvBytes = out[7].bytes;
	  //       numPairs = yuvBytes.length / (2 * 4);
   //      	System.out.println("[HISTOGRAM] yuvBytes: " + yuvBytes.length);
	  //       try {
	  //           DataInputStream dis = new DataInputStream(new ByteArrayInputStream(yuvBytes));
	  //           for (int i = 0; i < numPairs; i++) {
	  //           	Integer yuv_val_key = new Integer(dis.readInt());
	  //           	Integer yuv_val_val = new Integer(dis.readInt());
	  //           	yuv_line_vals.put(yuv_val_key, yuv_val_val);
	  //           }
	  //       } catch (Exception e) {
	  //           e.printStackTrace();
	  //       }	        

	        // get "green" image
			UV8image greenImg = new UV8image(320, 240, out[7].bytes, true);
            this.green_img = greenImg.toBufferedImage();

            // get all pixel u histogram values
	        u_all_vals = new TreeMap<Integer, Integer>();
	        byte[] uAllBytes = out[8].bytes;
	        int numUAllPairs = uAllBytes.length / (2 * 4);
        	System.out.println("[HISTOGRAM] uAllBytes: " + uAllBytes.length);
	        try {
	            DataInputStream dis = new DataInputStream(new ByteArrayInputStream(uAllBytes));

	            for (int i = 0; i < numUAllPairs; i++) {
	            	Integer u_val_key = new Integer(dis.readInt());
	            	Integer u_val_val = new Integer(dis.readInt());
	            	u_all_vals.put(u_val_key, u_val_val);
	            }
	        } catch (Exception e) {
	            e.printStackTrace();
	        }

            // get all pixels yuv histogram values
			// HashMap<Integer, Integer> all_pixel_y_vals = new HashMap<Integer, Integer>();
			// HashMap<Integer, Integer> all_pixel_u_vals = new HashMap<Integer, Integer>();
			// HashMap<Integer, Integer> all_pixel_v_vals = new HashMap<Integer, Integer>();
	  //       byte[] allPixBytes = out[8].bytes;
	  //       numPairs = allPixBytes.length / (4 * 4);
   //      	System.out.println("[HISTOGRAM] allPixBytes: " + allPixBytes.length);
	  //       try {
	  //           DataInputStream dis = new DataInputStream(new ByteArrayInputStream(yBytes));
	  //           for (int i = 0; i < numPairs; i++) {
	  //           	Integer y_val = new Integer(dis.readInt());
	  //           	Integer u_val = new Integer(dis.readInt());
	  //           	Integer v_val = new Integer(dis.readInt());
	  //           	Integer count = new Integer(dis.readInt());
	  //           	y_line_vals.put(y_val_key, y_val_val);
	  //           }
	  //       } catch (Exception e) {
	  //           e.printStackTrace();
	  //       }




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
		// label = String.format("(%d,%d): y=%d u=%d v=%d", col, row, y, u, v);
		repaint();
	}
	
}
