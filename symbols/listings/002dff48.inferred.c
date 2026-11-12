/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

int * FUN_002dff48(int *param_1)

{
  int *piVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  int iVar6;
  undefined1 auStack_14 [4];
  
  iVar4 = DAT_002e0128;
  iVar2 = DAT_002e0128 + 0x84;
  iVar3 = DAT_002e0128 + 0xa4;
  iVar5 = DAT_002e0128 + 200;
  *param_1 = DAT_002e0128;
  param_1[1] = iVar2;
  param_1[2] = iVar3;
  param_1[8] = iVar4 + 0xdc;
  param_1[10] = iVar4 + 0xec;
  param_1[3] = iVar5;
  param_1[0xb] = iVar4 + 0x11c;
  FUN_00627f38(param_1 + 0x39);
  FUN_00627f38(param_1 + 0x32);
  FUN_00627f38(param_1 + 0x2b);
  FUN_00627f38(param_1 + 0x24);
  FUN_00627f38(param_1 + 0x1d);
  FUN_00627f38(param_1 + 0x16);
  iVar2 = DAT_002e012c;
  iVar3 = DAT_002e012c + 0x58;
  iVar5 = DAT_002e012c + 0x68;
  iVar6 = DAT_002e012c + 0x98;
  *param_1 = iVar4 + 0x138;
  param_1[0xb] = iVar6;
  param_1[1] = iVar2;
  param_1[2] = iVar4 + 0x1c0;
  param_1[3] = iVar4 + 0x1e4;
  param_1[8] = iVar3;
  param_1[10] = iVar5;
  FUN_00695db8();
  iVar2 = DAT_002e0130;
  *param_1 = iVar4 + 0x200;
  param_1[10] = iVar2;
  iVar3 = DAT_002e0138;
  iVar2 = DAT_002e0134;
  param_1[2] = iVar4 + 0x240;
  param_1[1] = iVar2;
  param_1[8] = iVar3;
  param_1[3] = iVar4 + 0x264;
  do {
    iVar2 = param_1[7];
    iVar4 = (iVar2 + -1) * 4;
    do {
      if (iVar2 < 1) {
        free((void *)param_1[5]);
        iVar4 = DAT_002e013c;
        param_1[2] = DAT_002e013c + 0x18;
        iVar2 = DAT_002e0140;
        param_1[3] = iVar4;
        param_1[1] = iVar2;
        *param_1 = DAT_002e0144;
        if (param_1[0x3b] != 0x5e715e28) {
          FUN_00636880(auStack_14,iVar4 + -0x2a4);
          FUN_004f75c8(auStack_14);
        }
        param_1[0x3b] = 0;
        return param_1;
      }
      iVar2 = iVar2 + -1;
      param_1[7] = iVar2;
      piVar1 = (int *)(param_1[5] + iVar4);
      iVar4 = iVar4 + -4;
    } while ((int *)*piVar1 == (int *)0x0);
    (**(code **)(*(int *)*piVar1 + 4))();
  } while( true );
}

