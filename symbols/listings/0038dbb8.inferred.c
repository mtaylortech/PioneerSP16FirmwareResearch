/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

int * FUN_0038dbb8(int *param_1,undefined4 param_2,undefined4 param_3,int *param_4)

{
  int iVar1;
  int iVar2;
  uint uVar3;
  
  param_1[0x45] = 0x5e715e28;
  FUN_00760bc8();
  iVar2 = DAT_0038de44;
  iVar1 = DAT_0038de40;
  param_1[0x1e] = (int)param_4;
  param_1[0x1c] = iVar1;
  param_1[0x1d] = iVar2;
  if (param_4 != (int *)0x0) {
    if (((uint)param_4 & 3) == 0) {
      uVar3 = (int)param_4 + *(int *)(*param_4 + -0xc);
      if (((uVar3 != 0) && ((uVar3 & 3) == 0)) &&
         (*(int *)((int)param_4 + *(int *)(*param_4 + -0xc)) == 0x5e715e28)) {
        FUN_0038d6e8(param_4,param_1 + 0x1d);
        goto LAB_0038dc30;
      }
    }
    FUN_004f782c(DAT_0038de4c,DAT_0038de50,DAT_0038de54);
    param_1[0x1e] = 0;
  }
LAB_0038dc30:
  iVar1 = DAT_0038de48;
  *param_1 = DAT_0038de48 + -0x150;
  param_1[0x1f] = 0;
  param_1[0x1c] = iVar1 + -0x78;
  param_1[0x1d] = iVar1 + -0x50;
  param_1[0x20] = 0;
  param_1[0x21] = 0;
  FUN_006d3148(param_1 + 0x22);
  FUN_006d3148(param_1 + 0x23);
  FUN_006d3148(param_1 + 0x24);
  FUN_006d3148(param_1 + 0x25);
  FUN_006d3148(param_1 + 0x26);
  FUN_006d3148(param_1 + 0x27);
  FUN_006d3148(param_1 + 0x28);
  FUN_006d3148(param_1 + 0x29);
  FUN_006d3148(param_1 + 0x2a);
  FUN_006d3148(param_1 + 0x2b);
  FUN_006d3148(param_1 + 0x2c);
  FUN_006d3148(param_1 + 0x2d);
  FUN_006d3148(param_1 + 0x2e);
  FUN_006d3148(param_1 + 0x2f);
  FUN_006d3148(param_1 + 0x30);
  FUN_006d3148(param_1 + 0x31);
  FUN_006d3148(param_1 + 0x32);
  FUN_006d3148(param_1 + 0x33);
  FUN_006d3148(param_1 + 0x34);
  FUN_006d3148(param_1 + 0x35);
  FUN_006d3148(param_1 + 0x36);
  FUN_006d3148(param_1 + 0x37);
  FUN_006d3148(param_1 + 0x38);
  FUN_006d3148(param_1 + 0x39);
  FUN_006d3148(param_1 + 0x3a);
  FUN_006d3148(param_1 + 0x3b);
  FUN_006d3148(param_1 + 0x3c);
  FUN_006d3148(param_1 + 0x3d);
  FUN_006d3148(param_1 + 0x3e);
  FUN_006d3148(param_1 + 0x3f);
  *(undefined1 *)(param_1 + 0x40) = 0;
  *(undefined1 *)((int)param_1 + 0x101) = 0;
  FUN_00627ba0(param_1 + 0x41,param_2);
  param_1[0x42] = 0;
  param_1[0x43] = 0;
  param_1[0x44] = 0;
  FUN_00760d50(param_1,param_2);
  FUN_00760eb0(param_1,1,0);
  return param_1;
}

