/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

int candidate_0026cce0(int param_1,int param_2)

{
  int iVar1;
  undefined4 uVar2;
  int iVar3;
  
  iVar3 = param_1 + 0x20;
  iVar1 = FUN_002f32e8(iVar3);
  if (param_2 != iVar1) {
    iVar1 = param_1 + param_2 * 0x1c;
    *(undefined1 *)(iVar1 + 0x168) = 0;
    uVar2 = FUN_002f3fa0(iVar3,param_2);
    *(undefined4 *)(iVar1 + 0x174) = uVar2;
    return param_1 + param_2 * 0x1c + 0x168;
  }
  uVar2 = FUN_002f3ea0(iVar3,param_2,param_1 + param_2 * 0x1c + 0x168);
  *(undefined4 *)(param_1 + param_2 * 0x1c + 0x174) = uVar2;
  return param_1 + param_2 * 0x1c + 0x168;
}

