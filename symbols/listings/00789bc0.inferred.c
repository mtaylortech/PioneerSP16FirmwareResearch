/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_00789bc0(int *param_1)

{
  int iVar1;
  uint in_fpscr;
  float fVar2;
  float fVar3;
  float fVar4;
  float fVar5;
  undefined1 auStack_58 [24];
  undefined1 auStack_40 [24];
  undefined1 auStack_28 [8];
  int local_20;
  int local_1c;
  undefined1 auStack_14 [12];
  
  *(undefined4 *)(DAT_00789cb4 + 0x60) = *(undefined4 *)(DAT_00789cb4 + 0x13c);
  FUN_006cf7a8(auStack_14);
  if (*(int *)(param_1[1] + 0x24) != 0) {
    FUN_006c6158(auStack_58);
    FUN_006cfbc4(auStack_14,auStack_58);
  }
  (**(code **)(*param_1 + 0x20))(auStack_28,param_1);
  iVar1 = param_1[1];
  if ((local_20 != *(int *)(iVar1 + 0x18)) || (local_1c != *(int *)(iVar1 + 0x1c))) {
    fVar2 = (float)VectorSignedToFloat(local_20,(byte)(in_fpscr >> 0x16) & 3);
    fVar3 = (float)VectorSignedToFloat(*(int *)(iVar1 + 0x18),(byte)(in_fpscr >> 0x16) & 3);
    fVar4 = (float)VectorSignedToFloat(local_1c,(byte)(in_fpscr >> 0x16) & 3);
    fVar5 = (float)VectorSignedToFloat(*(int *)(iVar1 + 0x1c),(byte)(in_fpscr >> 0x16) & 3);
    FUN_006c67dc(auStack_40,fVar2 / fVar3,fVar4 / fVar5);
    FUN_006cfbc4(auStack_14,auStack_40);
    iVar1 = param_1[1];
  }
  FUN_00789950(iVar1,auStack_14,1);
  FUN_006cf7b8(auStack_14);
  return;
}

