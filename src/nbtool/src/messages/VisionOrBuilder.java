// Generated by the protocol buffer compiler.  DO NOT EDIT!
// source: Vision.proto

package messages;

public interface VisionOrBuilder extends
    // @@protoc_insertion_point(interface_extends:messages.Vision)
    com.google.protobuf.MessageOrBuilder {

  /**
   * <code>repeated .messages.FieldLine line = 1;</code>
   */
  java.util.List<messages.FieldLine> 
      getLineList();
  /**
   * <code>repeated .messages.FieldLine line = 1;</code>
   */
  messages.FieldLine getLine(int index);
  /**
   * <code>repeated .messages.FieldLine line = 1;</code>
   */
  int getLineCount();
  /**
   * <code>repeated .messages.FieldLine line = 1;</code>
   */
  java.util.List<? extends messages.FieldLineOrBuilder> 
      getLineOrBuilderList();
  /**
   * <code>repeated .messages.FieldLine line = 1;</code>
   */
  messages.FieldLineOrBuilder getLineOrBuilder(
      int index);

  /**
   * <code>repeated .messages.Corner corner = 2;</code>
   */
  java.util.List<messages.Corner> 
      getCornerList();
  /**
   * <code>repeated .messages.Corner corner = 2;</code>
   */
  messages.Corner getCorner(int index);
  /**
   * <code>repeated .messages.Corner corner = 2;</code>
   */
  int getCornerCount();
  /**
   * <code>repeated .messages.Corner corner = 2;</code>
   */
  java.util.List<? extends messages.CornerOrBuilder> 
      getCornerOrBuilderList();
  /**
   * <code>repeated .messages.Corner corner = 2;</code>
   */
  messages.CornerOrBuilder getCornerOrBuilder(
      int index);

  /**
   * <code>optional .messages.CenterCircle circle = 3;</code>
   */
  boolean hasCircle();
  /**
   * <code>optional .messages.CenterCircle circle = 3;</code>
   */
  messages.CenterCircle getCircle();
  /**
   * <code>optional .messages.CenterCircle circle = 3;</code>
   */
  messages.CenterCircleOrBuilder getCircleOrBuilder();

  /**
   * <code>optional .messages.VBall ball = 4;</code>
   */
  boolean hasBall();
  /**
   * <code>optional .messages.VBall ball = 4;</code>
   */
  messages.VBall getBall();
  /**
   * <code>optional .messages.VBall ball = 4;</code>
   */
  messages.VBallOrBuilder getBallOrBuilder();
}
