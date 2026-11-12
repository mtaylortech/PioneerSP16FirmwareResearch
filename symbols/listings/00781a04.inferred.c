/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

int * FUN_00781a04(int *param_1,int param_2)

{
  int *piVar1;
  int *piVar2;
  int iVar3;
  int *piVar4;
  int iVar5;
  int *local_28;
  undefined4 local_24;
  int local_20;
  
  if (param_1 != (int *)0x0) {
    iVar5 = 0;
    piVar1 = param_1;
    do {
      local_28 = (int *)0x0;
      local_24 = 0;
      local_20 = 0;
      (**(code **)(*piVar1 + 0xc))(piVar1,&local_28);
      if (local_28 != local_28 + local_20) {
        iVar3 = *local_28;
        piVar4 = local_28;
        piVar2 = local_28;
        while( true ) {
          if (param_2 == iVar3) goto LAB_00781b64;
          piVar4 = piVar4 + 1;
          if (local_28 + local_20 == piVar4) break;
          piVar2 = piVar2 + 1;
          iVar3 = *piVar2;
        }
      }
      piVar1 = (int *)(**(code **)(*piVar1 + 8))(piVar1);
      iVar5 = iVar5 + 1;
      if (param_1 == piVar1 || 100 < iVar5) {
        free(local_28);
        if (piVar1 != (int *)0x0) {
          return (int *)0x0;
        }
        break;
      }
      free(local_28);
    } while (piVar1 != (int *)0x0);
  }
  if (*DAT_00781ba4 == 0) {
    piVar1 = (int *)0x0;
  }
  else {
    piVar1 = (int *)__dynamic_cast(*DAT_00781ba4,DAT_00781ba8,DAT_00781bac,0);
    if (piVar1 != (int *)0x0) {
      local_28 = (int *)0x0;
      piVar4 = piVar1 + 4;
      piVar1 = piVar1 + 4;
      local_24 = 0;
      local_20 = 0;
      (**(code **)(*piVar4 + 0xc))(piVar1,&local_28);
      if (local_28 == local_28 + local_20) {
LAB_00781b60:
        piVar1 = (int *)0x0;
      }
      else {
        iVar5 = *local_28;
        piVar4 = local_28;
        piVar2 = local_28;
        while (param_2 != iVar5) {
          piVar4 = piVar4 + 1;
          if (local_28 + local_20 == piVar4) goto LAB_00781b60;
          piVar2 = piVar2 + 1;
          iVar5 = *piVar2;
        }
      }
LAB_00781b64:
      free(local_28);
    }
  }
  return piVar1;
}

