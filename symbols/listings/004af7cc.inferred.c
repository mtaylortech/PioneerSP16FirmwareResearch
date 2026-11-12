/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

undefined4 FUN_004af7cc(void)

{
  int iVar1;
  
  if (((*DAT_004af82c & 1) == 0) && (iVar1 = __cxa_guard_acquire(), iVar1 != 0)) {
    FUN_00666e84(DAT_004af830,DAT_004af834);
    __cxa_guard_release(DAT_004af82c);
    __aeabi_atexit(DAT_004af830,DAT_004af838,DAT_004af83c);
    return DAT_004af830;
  }
  return DAT_004af830;
}

