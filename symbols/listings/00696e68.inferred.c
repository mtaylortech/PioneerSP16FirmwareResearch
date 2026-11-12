/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

/* SUPPORTED ANALYST INTERPRETATION; address identity retained. Mutex-protected sorted pointer
   insertion. Original source signature is not recovered. */

void juce_register_listener_sorted_00696e68(int param_1,uint param_2)

{
  bool bVar1;
  void *__ptr;
  uint uVar2;
  int iVar3;
  uint *__src;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  
  pthread_mutex_lock((pthread_mutex_t *)(param_1 + 0x14));
  if (param_2 == 0) goto LAB_00696f38;
  uVar6 = *(uint *)(param_1 + 0x10);
  __ptr = *(void **)(param_1 + 8);
  uVar5 = uVar6;
  uVar2 = 0;
  while (uVar4 = uVar2, (int)uVar4 < (int)uVar5) {
    if (*(uint *)((int)__ptr + uVar4 * 4) == param_2) {
      *(uint *)((int)__ptr + uVar4 * 4) = param_2;
      goto LAB_00696f38;
    }
    while( true ) {
      uVar2 = (int)(uVar5 + uVar4) >> 1;
      bVar1 = *(uint *)((int)__ptr + uVar2 * 4) <= param_2;
      if (uVar2 == uVar4) {
        uVar2 = *(uint *)(param_1 + 0xc);
        if (bVar1) {
          uVar4 = uVar4 + 1;
        }
        if ((int)(uVar6 + 1) <= (int)uVar2) goto LAB_00696efc;
        goto LAB_00696f74;
      }
      if (bVar1) break;
      uVar5 = uVar2;
      if ((int)uVar2 <= (int)uVar4) goto LAB_00696eec;
    }
  }
LAB_00696eec:
  uVar2 = *(uint *)(param_1 + 0xc);
  if ((int)uVar2 < (int)(uVar6 + 1)) {
LAB_00696f74:
    uVar5 = uVar6 + 1 + (int)(uVar6 + 1) / 2 + 8 & 0xfffffff8;
    if (uVar2 == uVar5) goto LAB_00696efc;
    if ((int)uVar5 < 1) {
      free(__ptr);
      uVar6 = *(uint *)(param_1 + 0x10);
      __ptr = (void *)0x0;
    }
    else if (__ptr == (void *)0x0) {
      __ptr = malloc(uVar5 << 2);
    }
    else {
      __ptr = realloc(__ptr,uVar5 << 2);
      uVar6 = *(uint *)(param_1 + 0x10);
    }
    *(void **)(param_1 + 8) = __ptr;
    *(uint *)(param_1 + 0xc) = uVar5;
    if (uVar6 <= uVar4) goto LAB_00696f44;
  }
  else {
LAB_00696efc:
    if (uVar6 <= uVar4) {
LAB_00696f44:
      *(uint *)(param_1 + 0x10) = uVar6 + 1;
      if ((void *)((int)__ptr + uVar6 * 4) != (void *)0x0) {
        *(uint *)((int)__ptr + uVar6 * 4) = param_2;
      }
      goto LAB_00696f38;
    }
  }
  __src = (uint *)((int)__ptr + uVar4 * 4);
  if (0 < (int)(uVar6 - uVar4)) {
    memmove(__src + 1,__src,(uVar6 - uVar4) * 4);
  }
  iVar3 = *(int *)(param_1 + 0x10);
  if (__src != (uint *)0x0) {
    *__src = param_2;
  }
  *(int *)(param_1 + 0x10) = iVar3 + 1;
LAB_00696f38:
  pthread_mutex_unlock((pthread_mutex_t *)(param_1 + 0x14));
  return;
}

