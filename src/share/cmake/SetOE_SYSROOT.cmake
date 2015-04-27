# Sets value of OE_SYSROOT based on the AL_DIR env variable in nbites.bash

file (STRINGS "/home/nmorin/nbites/util/scripts/nbites.bash" BITES_BASH_SCRIPT NEWLINE_CONSUME)

if(${BITES_BASH_SCRIPT} MATCHES "2.1.0.19")
  message(STATUS "Setting v5 sysroot")
  set( OE_SYSROOT "${TOOLCHAIN_DIR}/libnaoqi-sysroot/" )
else()
  message(STATUS "Setting v4 sysroot")
  set( OE_SYSROOT "${TOOLCHAIN_DIR}/sysroot/" )
endif()

message(STATUS "If this is incorrect, change your nbites.bash")