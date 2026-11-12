/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

undefined1 FUN_002bffb0(int param_1,int param_2)

{
  undefined1 uVar1;
  void *__ptr;
  int iVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  
  iVar3 = *(int *)(param_1 + 0x40);
  iVar4 = *(int *)(iVar3 + 0xb8);
  if (iVar4 == 0) {
    __ptr = (void *)0x0;
  }
  else if (iVar4 < 1) {
    __ptr = (void *)0x0;
  }
  else {
    __ptr = malloc(iVar4 << 2);
    iVar5 = *(int *)(iVar3 + 0xb0);
    iVar2 = 0;
    iVar3 = 0;
    do {
      iVar3 = iVar3 + 1;
      if ((int)__ptr + iVar2 != 0) {
        *(undefined4 *)((int)__ptr + iVar2) = *(undefined4 *)(iVar5 + iVar2);
      }
      iVar2 = iVar2 + 4;
    } while (iVar3 != iVar4);
  }
  iVar3 = *(int *)((int)__ptr + (param_2 + -1) * 4);
  free(__ptr);
  if (iVar3 == 0) {
    return 0;
  }
  uVar1 = 0;
  if ((int)((uint)*(byte *)(iVar3 + 0x68) << 0x1e) < 0) {
    uVar1 = *(undefined1 *)(iVar3 + 200);
  }
  return uVar1;
}

