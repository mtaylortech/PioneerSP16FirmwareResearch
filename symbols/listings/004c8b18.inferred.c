/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_004c8b18(int *param_1,char *param_2)

{
  char cVar1;
  int iVar2;
  int iVar3;
  char cVar4;
  int iVar5;
  undefined1 auStack_1c [8];
  
  cVar1 = *param_2;
  if ((char)param_1[0x2b] == cVar1) {
    iVar5 = *(int *)(param_2 + 4);
    if (param_1[0x2c] == iVar5) {
      iVar3 = *(int *)(param_2 + 8);
      if (param_1[0x2d] == iVar3) {
        iVar2 = *(int *)(param_2 + 0xc);
        cVar4 = param_2[0x10];
        if (param_1[0x2e] == iVar2) {
          if ((char)param_1[0x2f] == cVar4) {
            iVar5 = FUN_0062e318(param_1 + 0x30,param_2 + 0x14);
            if ((iVar5 != 0) && (param_1[0x31] == *(int *)(param_2 + 0x18))) {
              return;
            }
            cVar1 = *param_2;
            iVar5 = *(int *)(param_2 + 4);
            iVar3 = *(int *)(param_2 + 8);
            iVar2 = *(int *)(param_2 + 0xc);
            cVar4 = param_2[0x10];
          }
        }
      }
      else {
        iVar2 = *(int *)(param_2 + 0xc);
        cVar4 = param_2[0x10];
      }
    }
    else {
      iVar3 = *(int *)(param_2 + 8);
      iVar2 = *(int *)(param_2 + 0xc);
      cVar4 = param_2[0x10];
    }
  }
  else {
    iVar5 = *(int *)(param_2 + 4);
    iVar3 = *(int *)(param_2 + 8);
    iVar2 = *(int *)(param_2 + 0xc);
    cVar4 = param_2[0x10];
  }
  param_1[0x2c] = iVar5;
  *(char *)(param_1 + 0x2f) = cVar4;
  *(char *)(param_1 + 0x2b) = cVar1;
  param_1[0x2d] = iVar3;
  param_1[0x2e] = iVar2;
  FUN_0062ab80(param_1 + 0x30,param_2 + 0x14);
  iVar5 = *(int *)param_1[0x34];
  param_1[0x31] = *(int *)(param_2 + 0x18);
  (**(code **)(iVar5 + 0x2c))((int *)param_1[0x34],(char)param_1[0x2b]);
  iVar5 = param_1[0x36];
  (**(code **)(*param_1 + 0xf4))(auStack_1c,param_1);
  FUN_0038eac8(iVar5,auStack_1c,0);
  FUN_00627f38(auStack_1c);
  FUN_00790630(param_1);
  return;
}

