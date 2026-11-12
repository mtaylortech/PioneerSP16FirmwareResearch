/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

/* WARNING: Unknown calling convention -- yet parameter storage is locked */
/* SUPPORTED ANALYST INTERPRETATION; address identity retained. r0 supplies thread object;
   pthread_create at 0064708c and detach on zero return. Original source signature is not recovered.
    */

void juce_start_thread_0064703c(void *thread)

{
  int iVar1;
  pthread_t pVar2;
  pthread_t local_1c [2];
  
  pthread_mutex_lock((pthread_mutex_t *)((int)thread + 0x10));
  *(undefined1 *)((int)thread + 0xd0) = 0;
  pVar2 = *(pthread_t *)((int)thread + 8);
  if (pVar2 == 0) {
    *(undefined4 *)((int)thread + 8) = 0;
    local_1c[0] = pVar2;
    iVar1 = pthread_create(local_1c,(pthread_attr_t *)0x0,DAT_006470fc,thread);
    if (iVar1 == 0) {
      pthread_detach(local_1c[0]);
      *(pthread_t *)((int)thread + 8) = local_1c[0];
      *(undefined4 *)((int)thread + 0xc) = *(undefined4 *)((int)thread + 8);
    }
    FUN_00646f84(*(undefined4 *)((int)thread + 8),*(undefined4 *)((int)thread + 200));
    pthread_mutex_lock((pthread_mutex_t *)((int)thread + 0x58));
    if (*(char *)((int)thread + 0x70) == '\0') {
      *(undefined1 *)((int)thread + 0x70) = 1;
      pthread_cond_broadcast((pthread_cond_t *)((int)thread + 0x28));
    }
    pthread_mutex_unlock((pthread_mutex_t *)((int)thread + 0x58));
  }
  pthread_mutex_unlock((pthread_mutex_t *)((int)thread + 0x10));
  return;
}

