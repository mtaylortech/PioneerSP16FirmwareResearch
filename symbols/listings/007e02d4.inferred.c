/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

undefined4 FUN_007e02d4(int *param_1,undefined4 *param_2,undefined4 param_3)

{
  int iVar1;
  int *piVar2;
  int *piVar3;
  undefined4 *puVar4;
  undefined4 *puVar5;
  undefined4 uVar6;
  undefined4 local_70;
  undefined4 local_6c;
  undefined4 local_68;
  undefined4 local_64;
  undefined4 local_60;
  undefined4 local_5c;
  undefined4 local_58;
  undefined1 local_54;
  undefined4 local_50;
  undefined4 local_48;
  undefined1 auStack_44 [4];
  undefined1 auStack_40 [4];
  undefined1 auStack_3c [4];
  void *local_38;
  undefined4 local_34;
  undefined4 local_30;
  undefined4 local_2c;
  
  local_48 = 0;
  FUN_0062ab08(auStack_44);
  FUN_0062ab08(auStack_40);
  FUN_0062ab08(auStack_3c);
  uVar6 = *param_2;
  local_38 = (void *)0x0;
  local_34 = 0;
  local_30 = 0;
  local_2c = 0;
  iVar1 = (**(code **)(*param_1 + 0xc))(param_1,uVar6);
  if (iVar1 == 0) {
    if ((*DAT_007e0494 != 0) &&
       (iVar1 = __dynamic_cast(*DAT_007e0494,DAT_007e0498,DAT_007e049c), iVar1 != 0)) {
      iVar1 = iVar1 + 0x10;
      goto LAB_007e033c;
    }
  }
  else {
LAB_007e033c:
    piVar2 = (int *)FUN_00781a04(iVar1,uVar6);
    if (piVar2 != (int *)0x0) {
      local_48 = uVar6;
      (**(code **)(*piVar2 + 0x10))(piVar2,uVar6,&local_48);
      local_50 = param_2[8];
      puVar4 = (undefined4 *)param_1[8];
      local_64 = param_2[3];
      local_70 = *param_2;
      local_68 = param_2[2];
      local_60 = param_2[4];
      local_5c = param_2[5];
      local_58 = param_2[6];
      local_54 = *(undefined1 *)(param_2 + 7);
      puVar5 = puVar4;
      if ((int)puVar4 < 1) {
        puVar5 = param_2;
      }
      local_6c = local_2c;
      if (0 < (int)puVar4) {
        while (((puVar5 = (undefined4 *)((int)puVar5 + -1), (int)puVar5 < (int)puVar4 ||
                (puVar5 = (undefined4 *)((int)puVar4 + -1), -1 < (int)puVar5)) &&
               (piVar3 = *(int **)(param_1[6] + (int)puVar5 * 4),
               (**(code **)(*piVar3 + 8))(piVar3,&local_70), 0 < (int)puVar5))) {
          puVar4 = (undefined4 *)param_1[8];
        }
      }
      uVar6 = FUN_007dfff4(piVar2,&local_70,param_3);
      FUN_00699b64(param_1);
      goto LAB_007e0428;
    }
  }
  uVar6 = 0;
LAB_007e0428:
  free(local_38);
  FUN_00627f38(auStack_3c);
  FUN_00627f38(auStack_40);
  FUN_00627f38(auStack_44);
  return uVar6;
}

