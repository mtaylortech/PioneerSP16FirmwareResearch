/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

void FUN_00699484(int param_1)

{
  bool bVar1;
  int *piVar2;
  int iVar3;
  int iVar4;
  int *piVar5;
  
  piVar2 = operator_new(8);
  iVar3 = DAT_00699544;
  piVar2[1] = 0;
  iVar4 = *(int *)(DAT_00699548 + 4);
  *piVar2 = iVar3;
  if (((iVar4 != 0) && (*(char *)(iVar4 + 4) == '\0')) && (iVar3 = FUN_006986a0(), iVar3 != 0)) {
    *(undefined1 *)(param_1 + 4) = 1;
    return;
  }
  piVar5 = piVar2 + 1;
  DataMemoryBarrier(0xf);
  do {
    bVar1 = (bool)hasExclusiveAccess(piVar5);
  } while (!bVar1);
  *piVar5 = *piVar5 + 1;
  DataMemoryBarrier(0xf);
  DataMemoryBarrier(0xf);
  do {
    iVar3 = *piVar5;
    bVar1 = (bool)hasExclusiveAccess(piVar5);
  } while (!bVar1);
  *piVar5 = iVar3 + -1;
  DataMemoryBarrier(0xf);
  if (iVar3 + -1 == 0) {
    (**(code **)(*piVar2 + 4))(piVar2);
  }
  *(undefined1 *)(param_1 + 4) = 1;
  return;
}

