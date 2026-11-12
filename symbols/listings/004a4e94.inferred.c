/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_004a4e94(int param_1,int param_2,uint param_3,int param_4,int param_5)

{
  uint uVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  int *piVar5;
  
  uVar2 = *(uint *)(param_1 + 0xb8);
  uVar3 = uVar2;
  if (uVar2 != param_3) {
    FUN_004f782c(DAT_004a5050,DAT_004a5054,DAT_004a5058);
    uVar2 = *(uint *)(param_1 + 0xb8);
    uVar3 = uVar2;
    if ((int)param_3 <= (int)uVar2) {
      uVar3 = param_3;
    }
  }
  if ((int)uVar3 < 1) {
    return;
  }
  if (param_5 == 0) {
    uVar1 = 0;
    uVar4 = 0;
    if (param_4 != 0) {
      while( true ) {
        if ((uVar1 < uVar2) &&
           (piVar5 = *(int **)(*(int *)(param_1 + 0xb0) + uVar1 * 4), piVar5 != (int *)0x0)) {
          (**(code **)(*piVar5 + 0xf8))(piVar5,param_2);
          FUN_004c95c4(piVar5,*(undefined1 *)(param_4 + uVar1));
        }
        uVar1 = uVar1 + 1;
        if (uVar1 == uVar3) break;
        uVar2 = *(uint *)(param_1 + 0xb8);
        param_2 = param_2 + 0x1c;
      }
      return;
    }
    while( true ) {
      if ((uVar4 < uVar2) &&
         (piVar5 = *(int **)(*(int *)(param_1 + 0xb0) + uVar4 * 4), piVar5 != (int *)0x0)) {
        (**(code **)(*piVar5 + 0xf8))(piVar5,param_2);
      }
      uVar4 = uVar4 + 1;
      if (uVar4 == uVar3) break;
      uVar2 = *(uint *)(param_1 + 0xb8);
      param_2 = param_2 + 0x1c;
    }
    return;
  }
  uVar1 = 0;
  if (param_4 != 0) {
    uVar1 = 0;
    while( true ) {
      if ((uVar1 < uVar2) &&
         (piVar5 = *(int **)(*(int *)(param_1 + 0xb0) + uVar1 * 4), piVar5 != (int *)0x0)) {
        (**(code **)(*piVar5 + 0xf8))(piVar5,param_2);
        FUN_004c95c4(piVar5,*(undefined1 *)(param_4 + uVar1));
        (**(code **)(*piVar5 + 0x2c))(piVar5,*(undefined1 *)(param_5 + uVar1));
      }
      uVar1 = uVar1 + 1;
      if (uVar1 == uVar3) break;
      uVar2 = *(uint *)(param_1 + 0xb8);
      param_2 = param_2 + 0x1c;
    }
    return;
  }
  while( true ) {
    if ((uVar1 < uVar2) &&
       (piVar5 = *(int **)(*(int *)(param_1 + 0xb0) + uVar1 * 4), piVar5 != (int *)0x0)) {
      (**(code **)(*piVar5 + 0xf8))(piVar5,param_2);
      (**(code **)(*piVar5 + 0x2c))(piVar5,*(undefined1 *)(param_5 + uVar1));
    }
    uVar1 = uVar1 + 1;
    if (uVar1 == uVar3) break;
    uVar2 = *(uint *)(param_1 + 0xb8);
    param_2 = param_2 + 0x1c;
  }
  return;
}

