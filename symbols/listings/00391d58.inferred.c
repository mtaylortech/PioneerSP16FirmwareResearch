/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

undefined4 FUN_00391d58(int *param_1,int *param_2,int param_3)

{
  int *piVar1;
  void *pvVar2;
  int iVar3;
  int iVar4;
  uint uVar5;
  int iVar6;
  
  if ((param_2 != (int *)0x0) && (((uint)param_2 & 3) == 0)) {
    uVar5 = (int)param_2 + *(int *)(*param_2 + -0xc);
    if ((uVar5 != 0) &&
       (((uVar5 & 3) == 0 && (*(int *)((int)param_2 + *(int *)(*param_2 + -0xc)) == 0x5e715e28)))) {
      iVar3 = param_1[0x26];
      if (iVar3 != 0) {
        FUN_007c1644(param_1,iVar3);
        (**(code **)(*(int *)param_1[0x26] + 0xb8))((int *)param_1[0x26],0);
      }
      FUN_007ccc24(param_1,param_2,0xffffffff);
      param_1[0x26] = (int)param_2;
      (**(code **)(*param_1 + 0x84))(param_1);
      piVar1 = (int *)param_1[0x2a];
      if ((piVar1 != (int *)0x0) && (iVar3 != 0)) {
        (**(code **)(*piVar1 + 0xc))(piVar1,iVar3,param_1[0x26],param_1,400);
      }
      if (*(int **)param_1[0x23] == param_2) {
        param_1[0x29] = 0;
      }
      else if ((param_3 != 0) && ((char)param_1[0x2b] != '\0')) {
        iVar4 = param_1[0x29];
        iVar6 = iVar4 + 1;
        if ((param_1[0x28] < iVar6) &&
           (uVar5 = iVar6 + iVar6 / 2 + 8U & 0xfffffff8, param_1[0x28] != uVar5)) {
          pvVar2 = (void *)param_1[0x27];
          if ((int)uVar5 < 1) {
            free(pvVar2);
            iVar4 = param_1[0x29];
            pvVar2 = (void *)0x0;
            param_1[0x28] = uVar5;
            param_1[0x27] = 0;
            iVar6 = iVar4 + 1;
          }
          else {
            if (pvVar2 == (void *)0x0) {
              pvVar2 = malloc(uVar5 << 2);
              param_1[0x27] = (int)pvVar2;
            }
            else {
              pvVar2 = realloc(pvVar2,uVar5 << 2);
              iVar4 = param_1[0x29];
              iVar6 = iVar4 + 1;
              param_1[0x27] = (int)pvVar2;
            }
            param_1[0x28] = uVar5;
          }
        }
        else {
          pvVar2 = (void *)param_1[0x27];
        }
        param_1[0x29] = iVar6;
        if ((void *)((int)pvVar2 + iVar4 * 4) != (void *)0x0) {
          *(int *)((int)pvVar2 + iVar4 * 4) = iVar3;
        }
      }
      (**(code **)(*(int *)param_1[0x26] + 0xb8))((int *)param_1[0x26],1);
      if ((int *)param_1[0x2c] != (int *)0x0) {
        (**(code **)(*(int *)param_1[0x2c] + 8))();
        return 1;
      }
      return 1;
    }
  }
  FUN_004f782c(DAT_00391f44,DAT_00391f48,DAT_00391f4c);
  return 0;
}

