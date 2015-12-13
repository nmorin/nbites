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
import javax.swing.JCheckBox;
import javax.swing.JPanel;
import javax.swing.JTextField;
import javax.swing.JButton;
import javax.swing.event.*;
import javax.swing.BorderFactory;
import javax.swing.border.*;

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
	BufferedImage green_weighted_img;
	BufferedImage green_uv_img;
	BufferedImage alt_img;
	BufferedImage original_image;

	TreeMap<Integer, Integer> u_line_vals;
	TreeMap<Integer, Integer> u_all_vals;
	TreeMap<Integer, Integer> uv_all_vals;

    private JSlider fieldUThreshSlider;
    private JSlider fieldUWeightedThreshSlider;
    private JSlider vUVFieldThreshSlider;
    private JSlider uUVFieldThreshSlider;
    private JTextField uTextField;
    private JCheckBox viewToggle;
    private JCheckBox viewToggle2;
    private JButton repaintButton;
    private JPanel controlPanel;

	// private String label = null;
	int MIN_BAR_WIDTH = 5;
	int YUV_BASIC_MODE = 1;
	int FIELD_COLOR_MODE = 2;
	int LINE_COLOR_MODE = 3;
	int VIEW_MODE = 1;

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

	void paintBasicMode(Graphics g, int width, int height) {
		if (u_img != null)
			g.drawImage(u_img, width + 5, 0, null);
		if (v_img != null)
			g.drawImage(v_img, width + 5, height + 5, null);
		if (y_img != null)
			g.drawImage(y_img, width + 5, 2*height + 10, null);
		fieldUWeightedThreshSlider.setVisible(false);
		fieldUThreshSlider.setVisible(false);

	}

	void paintLineMode(Graphics g, int width, int height) {
		fieldUWeightedThreshSlider.setVisible(false);
		fieldUThreshSlider.setVisible(false);

		if (alt_img != null) 
			g.drawImage(alt_img, 0, height + 5, null);
		drawHist(g, u_line_vals, 2*width + 10, 5, 450, 200, "u_line_vals");

	}

	void paintFieldMode(Graphics g, int width, int height) {
		fieldUWeightedThreshSlider.setVisible(true);
		fieldUThreshSlider.setVisible(true);

		if (u_img != null)
			g.drawImage(u_img, width + 5, 0, null);
		if (green_img != null)
			g.drawImage(green_img, 0, height + 10, null);
		if (green_weighted_img != null)
			g.drawImage(green_weighted_img, width + 5, height + 10, null);
		if (green_uv_img != null)
			g.drawImage(green_uv_img, width + 5, 2*height + 70, null);

		drawHist(g, u_all_vals, 2*width + 10, 5, 450, 200, "u_all_vals");

		drawHist(g, uv_all_vals, 2*width + 10, 260, 450, 200, "v_vals_in_u");

		// u threshold slider
		int sliderX = 5; 
		int sliderY = 2*height + 20;
		int sliderHeight = 15;
		int sliderWidth = 150;
		fieldUThreshSlider.setBounds(sliderX, sliderY, sliderWidth, sliderHeight);
		g.drawString("width of u threshold for fieldcolor", sliderX, sliderY + 25);
		g.drawString("Current value: " + fieldUThreshSlider.getValue(), sliderX, sliderY + 40);

		// draw repaint button
		// draw u initial value text field


		// draw weighted u slider
		sliderX += width + 5;
		fieldUWeightedThreshSlider.setBounds(sliderX, sliderY, sliderWidth, sliderHeight);
		g.drawString("width of u threshold for fieldcolor", sliderX, sliderY + 25);
		g.drawString("Current value: " + fieldUWeightedThreshSlider.getValue(), sliderX, sliderY + 40);

		// draw the two uv sliders
		int uvSliderX = width + 5;
		int uvSliderY = 3*height + 70;
		uUVFieldThreshSlider.setBounds(uvSliderX, uvSliderY, sliderWidth, sliderHeight);
		g.drawString("width of uUV threshold for fieldcolor", uvSliderX, uvSliderY + sliderHeight + 10);
		g.drawString("Current value: " + uUVFieldThreshSlider.getValue(), uvSliderX, uvSliderY + sliderHeight + 25);

		uvSliderY += sliderHeight + 35;
		vUVFieldThreshSlider.setBounds(uvSliderX, uvSliderY, sliderWidth, sliderHeight);
		g.drawString("width of vUV threshold for fieldcolor", uvSliderX, uvSliderY + sliderHeight + 10);
		g.drawString("Current value: " + vUVFieldThreshSlider.getValue(), uvSliderX, uvSliderY + sliderHeight + 25);

		g.drawString("** REMEMBER, current width of u threshold is: " + fieldUThreshSlider.getValue(), uvSliderX, uvSliderY + sliderHeight*5);


	}
	
	public void paintComponent(Graphics g) {
		super.paintComponent(g);
		int width = 0, height = 0;

		if (original_image != null) {
			width = original_image.getWidth() / 2;
			height = original_image.getHeight() / 2;
			g.drawImage(original_image, 0, 0, width, height, null);
		}

		if (VIEW_MODE == YUV_BASIC_MODE)
			paintBasicMode(g, width, height);
		else if (VIEW_MODE == LINE_COLOR_MODE)
			paintLineMode(g, width, height);
		else
			paintFieldMode(g, width, height);

		int pWidth = 70, pHeight = 120;
		controlPanel.setBackground(Color.white);
		controlPanel.setBorder(new EtchedBorder(EtchedBorder.RAISED));
		controlPanel.setBounds(5, 3*height + height/2, width - 10, pHeight);
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
		if (!uTextField.getText().equals("") && !uTextField.getText().equals("u max")) 
			uFieldVal = Integer.parseInt(uTextField.getText());

		SExpr newFieldParams = SExpr.newList(
			SExpr.newKeyValue("uThreshold", fieldUThreshSlider.getValue()),
			SExpr.newKeyValue("uWeightedThreshold", fieldUWeightedThreshSlider.getValue()),
			SExpr.newKeyValue("uUVThresh", uUVFieldThreshSlider.getValue()),
			SExpr.newKeyValue("vUVThresh", vUVFieldThreshSlider.getValue()),
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
	    
	    viewToggle = new JCheckBox("Field color");
	    viewToggle.addItemListener(new ItemListener() {
	        public void itemStateChanged(ItemEvent e) {         
	            VIEW_MODE = (e.getStateChange()==1 ? FIELD_COLOR_MODE : YUV_BASIC_MODE);
	            repaint();
	        }           
	      });

	    viewToggle2 = new JCheckBox("Line color");
	    viewToggle2.addItemListener(new ItemListener() {
	        public void itemStateChanged(ItemEvent e) {         
	            VIEW_MODE = (e.getStateChange()==1 ? LINE_COLOR_MODE : YUV_BASIC_MODE);
	            repaint();
	        }           
	      });


		fieldUThreshSlider = new JSlider(JSlider.HORIZONTAL, 0, 20, 3);
		fieldUWeightedThreshSlider = new JSlider(JSlider.HORIZONTAL, 0, 20, 3);
		uUVFieldThreshSlider = new JSlider(JSlider.HORIZONTAL, 0, 20, 3);
		vUVFieldThreshSlider = new JSlider(JSlider.HORIZONTAL, 0, 20, 3);

		fieldUThreshSlider.addChangeListener(slide);
		fieldUWeightedThreshSlider.addChangeListener(slide);
		uUVFieldThreshSlider.addChangeListener(slide);
		vUVFieldThreshSlider.addChangeListener(slide);

		add(fieldUThreshSlider);
		add(fieldUWeightedThreshSlider);
		add(uUVFieldThreshSlider);
		add(vUVFieldThreshSlider);
		

		uTextField = new JTextField("u max");
		repaintButton = new JButton("Repaint");
        repaintButton.addActionListener(new ActionListener() {
        public void actionPerformed(ActionEvent e) { 
        	adjustParams();      
        }});

        add(uTextField);
        // add(repaintButton);

	    controlPanel = new JPanel();
	    add(controlPanel);
	    uTextField.setAlignmentX( Component.LEFT_ALIGNMENT );
	    controlPanel.setLayout(new FlowLayout(FlowLayout.LEFT));
	    controlPanel.add(viewToggle);
	    controlPanel.add(viewToggle2);
	    controlPanel.add(uTextField);
	    // uTextField.setBounds(10, 50, 60, 20);
	    controlPanel.add(repaintButton);
	}

	@Override
	public void ioFinished(IOInstance instance) {}

	private void setHistogramVals(Map<Integer, Integer> valueMap, byte[] bytes) {
		int numPairs = bytes.length / (2 * 4);
    	// System.out.println("[HISTOGRAM] bytes: " + bytes.length);
        try {
            DataInputStream dis = new DataInputStream(new ByteArrayInputStream(bytes));

            for (int i = 0; i < numPairs; i++) {
            	Integer key_val = new Integer(dis.readInt());
            	Integer val_val = new Integer(dis.readInt());
            	valueMap.put(key_val, val_val);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
	}

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
	        setHistogramVals(u_line_vals, out[4].bytes);

	        // Get v histogram vals -- lines
			HashMap<Integer, Integer> v_line_vals = new HashMap<Integer, Integer>();
	        setHistogramVals(v_line_vals, out[5].bytes);      

	        // Get y histogram vals -- lines
			HashMap<Integer, Integer> y_line_vals = new HashMap<Integer, Integer>();
	        setHistogramVals(y_line_vals, out[6].bytes);

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
	        setHistogramVals(u_all_vals, out[8].bytes);

	        // get "green" image with weighted func
			UV8image greenWeightedImg = new UV8image(320, 240, out[9].bytes, true);
            this.green_weighted_img = greenWeightedImg.toBufferedImage();

            // get all pixel uv histogram values
	        uv_all_vals = new TreeMap<Integer, Integer>();
	        setHistogramVals(uv_all_vals, out[10].bytes);

	        // get "green" image with both u and v filters
			UV8image greenUVImage = new UV8image(320, 240, out[11].bytes, true);
            this.green_uv_img = greenUVImage.toBufferedImage();

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
