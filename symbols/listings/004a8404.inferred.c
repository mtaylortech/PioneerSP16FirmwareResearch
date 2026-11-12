/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_004a8404(void)

{
  int iVar1;
  undefined4 in_r3;
  code *pcVar2;
  int iVar3;
  
  iVar1 = DAT_004a847c;
  iVar3 = DAT_004a8478;
  do {
    pcVar2 = *(code **)(iVar3 + -8);
    if (pcVar2 != (code *)0x0) {
      (*pcVar2)(iVar3 + -0x10,iVar3 + -0x10,3,pcVar2,in_r3);
    }
    if (*(code **)(iVar3 + -0x1c) != (code *)0x0) {
      (**(code **)(iVar3 + -0x1c))(iVar3 + -0x24,iVar3 + -0x24,3);
    }
    iVar3 = iVar3 + -0x28;
  } while (iVar3 != iVar1);
  return;
}

