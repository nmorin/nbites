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
import java.util.ArrayList;
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

public class ColorLearningView extends ViewParent implements MouseMotionListener, MouseListener, IOFirstResponder {
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
	TreeMap<Integer, Integer> v_line_vals;
	TreeMap<Integer, Integer> y_line_vals;
	ArrayList<Point> greenPixels;

    private JSlider fieldUThreshSlider;
    private JSlider fieldUWeightedThreshSlider;
    private JSlider vUVFieldThreshSlider;
    private JSlider uUVFieldThreshSlider;
    private JTextField uTextField;
    private JTextField yMinTextField;
    private JTextField saveFileNameTextField;
    private JCheckBox saveUVStateCheckBox;
    private JCheckBox viewToggle;
    private JCheckBox viewToggle2;
    private JButton repaintButton;
    // private JButton processGreenButton;
    private JPanel controlPanel;

	// private String label = null;
	int MIN_BAR_WIDTH = 5;
	int YUV_BASIC_MODE = 1;
	int FIELD_COLOR_MODE = 2;
	int LINE_COLOR_MODE = 3;
	int VIEW_MODE = 1;

	int ORG_IMG_SCALE_FACTOR = 2;

	boolean SAVE_UV_STATE = false;

	double calcStandDev(TreeMap<Integer, Integer> map) {
		ArrayList<Integer> differences = new ArrayList<>();
		int average = calcAvg(map);
		if (average == -1) return -1;
		for (Integer key : map.keySet()) {
			int count = map.get(key);
			for (int i = 0; i < count; i++) {
				int diff = key - average;
				diff = diff * diff;
				differences.add(diff);
			}
		}

		double avgDiff = 0;
		for (Integer num : differences) {
			avgDiff += num.doubleValue();
		}
		if (differences.size() == 0) return -1;
		avgDiff = avgDiff / ((double)differences.size());

		return Math.sqrt(avgDiff);
		
	}

	int calcAvg(TreeMap<Integer, Integer> map) {
		int sum = 0, count = 0;
		for (Integer key : map.keySet()) {
			int value = map.get(key);
			sum += key * value;
			count += value; 
		}
		if (count == 0) return -1;
		return (sum / count);
	}

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
            int average = calcAvg(vals_map);
            double stDev = calcStandDev(vals_map);
            String maxInfo = "Mode: " + mapMax;
            String meanInfo = "Mean: " + average;
            String sdInfo = "S Dev: " + stDev;
            g2d.drawString(maxInfo, xOffset + 25, yOffset + height + 40);
            g2d.drawString(meanInfo, xOffset + 25, yOffset + height + 50);
            g2d.drawString(sdInfo, xOffset + 25, yOffset + height + 60);


            int labelCount = 0;
            for (Integer key : vals_map.keySet()) {
                int value = vals_map.get(key);
                int barHeight = Math.round(((float) value / (float) maxValue) * height);
                if (key <= 255 && key >= 0)
	                g2d.setColor(new Color(key, key, key));
	            else
	            	g2d.setColor(Color.white);
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
		uUVFieldThreshSlider.setVisible(false);
		vUVFieldThreshSlider.setVisible(false);

	}

	void paintLineMode(Graphics g, int width, int height) {
		fieldUWeightedThreshSlider.setVisible(false);
		fieldUThreshSlider.setVisible(false);
		uUVFieldThreshSlider.setVisible(false);
		vUVFieldThreshSlider.setVisible(false);

		if (alt_img != null) 
			g.drawImage(alt_img, 0, height + 5, null);

		int histX = 2*width+10;
		int histY = 5;
		int histHeight = 200;
		int histWidth = 450;
		drawHist(g, u_line_vals, histX, histY, histWidth, histHeight, "u_line_vals");
		drawHist(g, v_line_vals, histX, histHeight + 100, histWidth, histHeight, "v_line_vals");
		drawHist(g, y_line_vals, histX - histWidth/3, 2*histHeight + 200, histWidth + histWidth/3, histHeight, "y_line_vals");
		// TODO y histogram not looking gr8
	}

	// void paintFieldMode(Graphics g, int width, int height) {
	// 	fieldUWeightedThreshSlider.setVisible(true);
	// 	fieldUThreshSlider.setVisible(true);
	// 	uUVFieldThreshSlider.setVisible(true);
	// 	vUVFieldThreshSlider.setVisible(true);

	// 	if (u_img != null)
	// 		g.drawImage(u_img, width + 5, 0, null);
	// 	if (green_img != null)
	// 		g.drawImage(green_img, 0, height + 10, null);
	// 	if (green_weighted_img != null)
	// 		g.drawImage(green_weighted_img, width + 5, height + 10, null);
	// 	if (green_uv_img != null)
	// 		g.drawImage(green_uv_img, width + 5, 2*height + 70, null);

	// 	drawHist(g, u_all_vals, 2*width + 10, 5, 450, 200, "u_all_vals");

	// 	drawHist(g, uv_all_vals, 2*width + 10, 300, 450, 200, "v_vals_in_u");

	// 	// u threshold slider
	// 	int sliderX = 5; 
	// 	int sliderY = 2*height + 20;
	// 	int sliderHeight = 15;
	// 	int sliderWidth = 150;
	// 	fieldUThreshSlider.setBounds(sliderX, sliderY, sliderWidth, sliderHeight);
	// 	g.drawString("width of u threshold for fieldcolor", sliderX, sliderY + 25);
	// 	g.drawString("Current value: " + fieldUThreshSlider.getValue(), sliderX, sliderY + 40);

	// 	// draw repaint button
	// 	// draw u initial value text field


	// 	// draw weighted u slider
	// 	sliderX += width + 5;
	// 	fieldUWeightedThreshSlider.setBounds(sliderX, sliderY, sliderWidth, sliderHeight);
	// 	g.drawString("width of u threshold for fieldcolor", sliderX, sliderY + 25);
	// 	g.drawString("Current value: " + fieldUWeightedThreshSlider.getValue(), sliderX, sliderY + 40);

	// 	// draw the two uv sliders
	// 	int uvSliderX = width + 5;
	// 	int uvSliderY = 3*height + 70;
	// 	uUVFieldThreshSlider.setBounds(uvSliderX, uvSliderY, sliderWidth, sliderHeight);
	// 	g.drawString("width of uUV threshold for fieldcolor", uvSliderX, uvSliderY + sliderHeight + 10);
	// 	g.drawString("Current value: " + uUVFieldThreshSlider.getValue(), uvSliderX, uvSliderY + sliderHeight + 25);

	// 	uvSliderY += sliderHeight + 35;
	// 	vUVFieldThreshSlider.setBounds(uvSliderX, uvSliderY, sliderWidth, sliderHeight);
	// 	g.drawString("width of vUV threshold for fieldcolor", uvSliderX, uvSliderY + sliderHeight + 10);
	// 	g.drawString("Current value: " + vUVFieldThreshSlider.getValue(), uvSliderX, uvSliderY + sliderHeight + 25);

	// 	g.drawString("** REMEMBER, current width of u threshold is: " + fieldUThreshSlider.getValue(), uvSliderX, uvSliderY + sliderHeight*5);


	// }
	
	public void paintComponent(Graphics g) {
		super.paintComponent(g);
		int width = 0, height = 0;

		if (original_image != null) {
			width = original_image.getWidth() / ORG_IMG_SCALE_FACTOR;
			height = original_image.getHeight() / ORG_IMG_SCALE_FACTOR;
			g.drawImage(original_image, 0, 0, width, height, null);
		}

		if (VIEW_MODE == YUV_BASIC_MODE)
			paintBasicMode(g, width, height);
		else if (VIEW_MODE == LINE_COLOR_MODE)
			paintLineMode(g, width, height);

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

		int yMinVal = 0;
		if (!yMinTextField.getText().equals("") && !yMinTextField.getText().equals("y min")) 
			yMinVal = Integer.parseInt(yMinTextField.getText());

		String saveFileName = "";
		if (!saveFileNameTextField.getText().equals("") && !saveFileNameTextField.getText().equals("csv file name")) 
			saveFileName = saveFileNameTextField.getText();

		String pixList = "";
		if (!greenPixels.isEmpty()) {
			Point pnt;
			
			for (int i = 0; i < greenPixels.size(); i++) {
				pnt = greenPixels.get(i);
				pixList += pnt.x + ":" + pnt.y + " ";
			}
		}
		SExpr newFieldParams;
		if (!saveFileName.equals("") && greenPixels.isEmpty()) {
			newFieldParams = SExpr.newList(
				SExpr.newKeyValue("saveFileName", saveFileName),
				SExpr.newKeyValue("yMinVal", yMinVal)//,
				// SExpr.newKeyValue("useGreen", pixList)
			);
		} else if (!greenPixels.isEmpty() && saveFileName.equals("")) {
			newFieldParams = SExpr.newList(
				// SExpr.newKeyValue("saveFileName", saveFileName),
				SExpr.newKeyValue("yMinVal", yMinVal),
				SExpr.newKeyValue("useGreen", pixList)
			);
		} else if (!greenPixels.isEmpty() && !saveFileName.equals("")) {
			System.out.println("[COLOR DEBUG] BOTH WERE TRUE, saving and green pixels");
			newFieldParams = SExpr.newList(
				SExpr.newKeyValue("saveFileName", saveFileName),
				SExpr.newKeyValue("useGreen", pixList)
			);
		}
		else {
			newFieldParams = SExpr.newList(
			SExpr.newKeyValue("yMinVal", yMinVal)//,
			// SExpr.newKeyValue("useGreen", pixList)
		);
		}
		

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
		this.addMouseListener(this);

		greenPixels = new ArrayList<>();

		ChangeListener slide = new ChangeListener(){
	        public void stateChanged(ChangeEvent e) {
	            adjustParams();
	        }
	    };
	    
	    // viewToggle = new JCheckBox("Field color");
	    // viewToggle.addItemListener(new ItemListener() {
	    //     public void itemStateChanged(ItemEvent e) {         
	    //         VIEW_MODE = (e.getStateChange()==1 ? FIELD_COLOR_MODE : YUV_BASIC_MODE);
	    //         repaint();
	    //     }           
	    //   });

	    viewToggle2 = new JCheckBox("Line color");
	    viewToggle2.addItemListener(new ItemListener() {
	        public void itemStateChanged(ItemEvent e) {         
	            VIEW_MODE = (e.getStateChange()==1 ? LINE_COLOR_MODE : YUV_BASIC_MODE);
	            repaint();
	        }           
	      });

	    saveUVStateCheckBox = new JCheckBox("Line color");
	    saveUVStateCheckBox.addItemListener(new ItemListener() {
	        public void itemStateChanged(ItemEvent e) {         
	            SAVE_UV_STATE = (e.getStateChange()==1 ? true : false);
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
		

		uTextField = new JTextField("u max", 4);
		yMinTextField = new JTextField("y min", 4);
		saveFileNameTextField = new JTextField("csv file name", 15);
		repaintButton = new JButton("Repaint");
        repaintButton.addActionListener(new ActionListener() {
        public void actionPerformed(ActionEvent e) { 
        	adjustParams();      
        }});

        add(uTextField);
        add(saveFileNameTextField);

	    controlPanel = new JPanel();
	    add(controlPanel);
	    uTextField.setAlignmentX( Component.LEFT_ALIGNMENT );
	    controlPanel.setLayout(new FlowLayout(FlowLayout.LEFT));
	    // controlPanel.add(viewToggle);
	    controlPanel.add(viewToggle2);
	    controlPanel.add(uTextField);
	    controlPanel.add(yMinTextField);
	    // uTextField.setBounds(10, 50, 60, 20);
	    controlPanel.add(repaintButton);
	    controlPanel.add(saveFileNameTextField);


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
		// TODO put in named constants instead of magic numbers... :/

		if (out.length > 0 && this.log.primaryFrom().equals("camera_TOP")) {
            UV8image u8 = new UV8image(320, 240, out[0].bytes, true, false);
            this.u_img = u8.toBufferedImage();

            UV8image v8 = new UV8image(320, 240, out[1].bytes, false, false);
            this.v_img = v8.toBufferedImage();

            Y16image yImg = new Y16image(320, 240, out[2].bytes);
            this.y_img = yImg.toBufferedImage();

            UV8image altImg = new UV8image(320, 240, out[3].bytes, true, false);
            this.alt_img = altImg.toBufferedImage();

            // Line histogram data:
        	// Get u histogram vals -- lines
	        u_line_vals = new TreeMap<Integer, Integer>();
	        setHistogramVals(u_line_vals, out[4].bytes);

	        // Get v histogram vals -- lines
			v_line_vals = new TreeMap<Integer, Integer>();
	        setHistogramVals(v_line_vals, out[5].bytes);      

	        // Get y histogram vals -- lines
			y_line_vals = new TreeMap<Integer, Integer>();
	        setHistogramVals(y_line_vals, out[6].bytes);
	    }
	    else if (out.length > 0 && this.log.primaryFrom().equals("camera_BOT")) {
	    	System.out.println("[COLORLEARN DEBUG] Bottom camera output!");
	    	UV8image u8 = new UV8image(160, 120, out[0].bytes, true, false);
            this.u_img = u8.toBufferedImage();

            UV8image v8 = new UV8image(160, 120, out[1].bytes, false, false);
            this.v_img = v8.toBufferedImage();

            Y16image yImg = new Y16image(160, 120, out[2].bytes);
            this.y_img = yImg.toBufferedImage();

            UV8image altImg = new UV8image(160, 120, out[3].bytes, true, false);
            this.alt_img = altImg.toBufferedImage();

            // Line histogram data:
        	// Get u histogram vals -- lines
	        u_line_vals = new TreeMap<Integer, Integer>();
	        setHistogramVals(u_line_vals, out[4].bytes);

	        // Get v histogram vals -- lines
			v_line_vals = new TreeMap<Integer, Integer>();
	        setHistogramVals(v_line_vals, out[5].bytes);      

	        // Get y histogram vals -- lines
			y_line_vals = new TreeMap<Integer, Integer>();
	        setHistogramVals(y_line_vals, out[6].bytes);


	    }
        else {
			System.out.println("ERROR no output received");
        }
		repaint();
	}

	@Override
	public boolean ioMayRespondOnCenterThread(IOInstance inst) {
		return false;
	}


	@Override
	public void mousePressed(MouseEvent e) {

		int SELECT_SIZE = 2;


		int origX = e.getX()/ (original_image.getWidth()) / ORG_IMG_SCALE_FACTOR;
		int origY = e.getY()/ (original_image.getHeight()) / ORG_IMG_SCALE_FACTOR;

		int col = (e.getX()*original_image.getWidth() / (original_image.getWidth() / ORG_IMG_SCALE_FACTOR));
		int row = e.getY()*original_image.getHeight() / (original_image.getHeight() / ORG_IMG_SCALE_FACTOR);
		if ((col < 0 + SELECT_SIZE || row < 0 + SELECT_SIZE || 
			col >= original_image.getWidth() - SELECT_SIZE || 
			row >= original_image.getHeight() - SELECT_SIZE)) {
			return;
		}

		int r = 250;
		int color = r << 16;
		for (int i = -SELECT_SIZE; i <= SELECT_SIZE; i++) {
			for (int j = -SELECT_SIZE; j <= SELECT_SIZE; j++) {
				original_image.setRGB(col + i, row + j, Color.red.getRGB());
				
				
			}
		}
		Point pix = new Point(origX, origY);
		if (!greenPixels.contains(pix)) {
			greenPixels.add(pix);
		}

	}

    public void mouseReleased(MouseEvent e) {
    }

    public void mouseEntered(MouseEvent e) {
    }

    public void mouseExited(MouseEvent e) {
    }

    public void mouseClicked(MouseEvent e) {
    }

	@Override
	public void mouseDragged(MouseEvent e) {

		int SELECT_SIZE = 5;

		int col = (e.getX()*original_image.getWidth() / (original_image.getWidth() / ORG_IMG_SCALE_FACTOR));
		int row = e.getY()*original_image.getHeight() / (original_image.getHeight() / ORG_IMG_SCALE_FACTOR);

		int origX = e.getX(); /// (original_image.getWidth()) / ORG_IMG_SCALE_FACTOR;
		int origY = e.getY(); /// (original_image.getHeight()) / ORG_IMG_SCALE_FACTOR;

		if ((col < 0 + SELECT_SIZE || row < 0 + SELECT_SIZE || 
			col >= original_image.getWidth() - SELECT_SIZE || 
			row >= original_image.getHeight() - SELECT_SIZE)) {
			return;
		}

		int r = 250;
		int color = r << 16;
		for (int i = -SELECT_SIZE; i <= SELECT_SIZE; i++) {
			for (int j = -SELECT_SIZE; j <= SELECT_SIZE; j++) {
				original_image.setRGB(col + i, row + j, Color.red.getRGB());
				// System.out.println("origX: " + origX + " origY: " + origY);
				Point pix = new Point(origX+i, origY+j);
				if (!greenPixels.contains(pix)) {
					greenPixels.add(pix);
				}
			}
		}
		
		repaint();

	}

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
