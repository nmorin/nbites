# Sets value of OE_SYSROOT based on the AL_DIR env variable

if($ENV{AL_DIR} MATCHES "2.1.0.19")
  message(STATUS "AL_DIR set to v5")
  set( OE_SYSROOT "${TOOLCHAIN_DIR}/libnaoqi-sysroot/" )
else()
  message(STATUS "AL_DIR set to v4")
  set( OE_SYSROOT "${TOOLCHAIN_DIR}/sysroot/" )
endif($ENV{AL_DIR} MATCHES "2.1.0.19")

message(STATUS "Here now")