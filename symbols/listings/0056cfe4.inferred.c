/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

/* WARNING: Unknown calling convention -- yet parameter storage is locked */
/* SUPPORTED ANALYST INTERPRETATION; address identity retained. Tail branch to 0064703c after
   optional stop request; thread startup does not establish worker completion. Original source
   signature is not recovered. */

void UIThread_start_0056cfe4(void *thread)

{
  if (*(char *)((int)thread + 0xd0) != '\0') {
    FUN_00639288(thread,0xffffffff);
  }
  juce_start_thread_0064703c(thread);
  return;
}

