// Generated by the protocol buffer compiler.  DO NOT EDIT!
// source: PMotion.proto

package messages;

public interface DestinationWalkOrBuilder extends
    // @@protoc_insertion_point(interface_extends:messages.DestinationWalk)
    com.google.protobuf.MessageOrBuilder {

  /**
   * <code>optional float rel_x = 1;</code>
   */
  boolean hasRelX();
  /**
   * <code>optional float rel_x = 1;</code>
   */
  float getRelX();

  /**
   * <code>optional float rel_y = 2;</code>
   */
  boolean hasRelY();
  /**
   * <code>optional float rel_y = 2;</code>
   */
  float getRelY();

  /**
   * <code>optional float rel_h = 3;</code>
   */
  boolean hasRelH();
  /**
   * <code>optional float rel_h = 3;</code>
   */
  float getRelH();

  /**
   * <code>optional float gain = 4;</code>
   */
  boolean hasGain();
  /**
   * <code>optional float gain = 4;</code>
   */
  float getGain();

  /**
   * <code>optional .messages.MotionKick kick = 5;</code>
   */
  boolean hasKick();
  /**
   * <code>optional .messages.MotionKick kick = 5;</code>
   */
  messages.MotionKick getKick();
  /**
   * <code>optional .messages.MotionKick kick = 5;</code>
   */
  messages.MotionKickOrBuilder getKickOrBuilder();
}
