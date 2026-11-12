/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

/* WARNING: Unknown calling convention -- yet parameter storage is locked */
/* SUPPORTED ANALYST INTERPRETATION; address identity retained. Integer milliseconds converted to
   timespec; nanosleep result ignored. Original source signature is not recovered. */

void sleep_milliseconds_006457dc(int milliseconds)

{
  timespec local_10;
  
  local_10.tv_sec = milliseconds / 1000;
  local_10.tv_nsec = (milliseconds % 1000) * 1000000;
  nanosleep(&local_10,(timespec *)0x0);
  return;
}

