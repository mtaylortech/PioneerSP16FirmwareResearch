/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_00392c2c(int *param_1,int *param_2,int param_3)

{
  bool bVar1;
  int *piVar2;
  int iVar3;
  void *pvVar4;
  int *piVar5;
  int *piVar6;
  code *pcVar7;
  int *piVar8;
  int *piVar9;
  uint uVar10;
  int iVar11;
  uint uVar12;
  uint uVar13;
  uint uVar14;
  
  if (param_3 == 0) {
    iVar11 = param_1[0x25];
    piVar2 = (int *)param_1[0x23];
    iVar3 = iVar11 * 4;
    piVar5 = piVar2 + iVar11;
    if (piVar2 == piVar5) {
LAB_00392d9c:
      iVar11 = iVar11 + 1;
      if ((param_1[0x24] < iVar11) &&
         (uVar14 = iVar11 + iVar11 / 2 + 8U & 0xfffffff8, param_1[0x24] != uVar14)) {
        if ((int)uVar14 < 1) {
          free(piVar2);
          pvVar4 = (void *)0x0;
          param_1[0x23] = 0;
          iVar11 = param_1[0x25] + 1;
          iVar3 = param_1[0x25] << 2;
        }
        else {
          if (piVar2 == (int *)0x0) {
            pvVar4 = malloc(uVar14 << 2);
          }
          else {
            pvVar4 = realloc(piVar2,uVar14 << 2);
            iVar11 = param_1[0x25] + 1;
            iVar3 = param_1[0x25] << 2;
          }
          param_1[0x23] = (int)pvVar4;
        }
        param_1[0x24] = uVar14;
        piVar5 = (int *)((int)pvVar4 + iVar3);
      }
      param_1[0x25] = iVar11;
      *piVar5 = (int)param_2;
      if (param_2 != (int *)0x0) {
        piVar2 = param_2 + 0x1d;
        DataMemoryBarrier(0xf);
        do {
          bVar1 = (bool)hasExclusiveAccess(piVar2);
        } while (!bVar1);
        *piVar2 = *piVar2 + 1;
        DataMemoryBarrier(0xf);
        param_2[0x1e] = (int)param_1;
        return;
      }
    }
    else {
      piVar6 = (int *)*piVar2;
      piVar9 = piVar2;
      piVar8 = piVar2;
      while (param_2 != piVar6) {
        piVar9 = piVar9 + 1;
        if (piVar5 == piVar9) goto LAB_00392d9c;
        piVar8 = piVar8 + 1;
        piVar6 = (int *)*piVar8;
      }
    }
    goto LAB_00392d4c;
  }
  uVar14 = param_1[0x25];
  piVar2 = (int *)param_1[0x23];
  piVar5 = piVar2 + uVar14;
  if (piVar2 == piVar5) {
LAB_00392c84:
    uVar12 = param_1[0x24];
    piVar9 = (int *)0x0;
LAB_00392c8c:
    iVar3 = uVar14 + 1;
    uVar10 = uVar14 & (int)uVar14 >> 0x1f;
    if ((int)uVar12 < iVar3) {
LAB_00392e84:
      uVar13 = iVar3 + iVar3 / 2 + 8U & 0xfffffff8;
      if (uVar13 != uVar12) {
        if ((int)uVar13 < 1) {
          free(piVar2);
          uVar14 = param_1[0x25];
          piVar2 = (int *)0x0;
        }
        else if (piVar2 == (int *)0x0) {
          piVar2 = malloc(uVar13 << 2);
        }
        else {
          piVar2 = realloc(piVar2,uVar13 << 2);
          uVar14 = param_1[0x25];
        }
        param_1[0x23] = (int)piVar2;
        param_1[0x24] = uVar13;
      }
    }
  }
  else {
    piVar6 = (int *)*piVar2;
    piVar9 = piVar2;
    piVar8 = piVar2;
    while (param_2 != piVar6) {
      piVar9 = piVar9 + 1;
      if (piVar5 == piVar9) goto LAB_00392c84;
      piVar8 = piVar8 + 1;
      piVar6 = (int *)*piVar8;
    }
    if ((int)piVar9 - (int)piVar2 < 0) goto LAB_00392c84;
    if (param_2 != (int *)0x0) {
      piVar2 = param_2 + 0x1d;
      DataMemoryBarrier(0xf);
      do {
        bVar1 = (bool)hasExclusiveAccess(piVar2);
      } while (!bVar1);
      *piVar2 = *piVar2 + 1;
      DataMemoryBarrier(0xf);
      uVar14 = param_1[0x25];
      piVar2 = (int *)param_1[0x23];
      piVar5 = piVar2 + uVar14;
    }
    piVar9 = param_2;
    if (piVar2 != piVar5) {
      piVar8 = piVar2;
      piVar6 = piVar2;
      if (param_2 == (int *)*piVar2) {
        uVar12 = 0;
      }
      else {
        do {
          piVar6 = piVar6 + 1;
          if (piVar6 == piVar5) goto LAB_00392e70;
          piVar8 = piVar8 + 1;
        } while (param_2 != (int *)*piVar8);
        uVar12 = (int)piVar6 - (int)piVar2 >> 2;
      }
      if (uVar14 <= uVar12) goto LAB_00392e70;
      piVar5 = (int *)piVar2[uVar12];
      if (piVar5 != (int *)0x0) {
        piVar8 = piVar5 + 0x1d;
        DataMemoryBarrier(0xf);
        do {
          iVar3 = *piVar8;
          bVar1 = (bool)hasExclusiveAccess(piVar8);
        } while (!bVar1);
        *piVar8 = iVar3 + -1;
        DataMemoryBarrier(0xf);
        if (iVar3 + -1 == 0) {
          (**(code **)(*piVar5 + 4))(piVar5);
        }
        uVar14 = param_1[0x25];
      }
      uVar14 = uVar14 - 1;
      param_1[0x25] = uVar14;
      if (0 < (int)(uVar14 - uVar12)) {
        memmove(piVar2 + uVar12,piVar2 + uVar12 + 1,(uVar14 - uVar12) * 4);
        uVar14 = param_1[0x25];
      }
      uVar12 = param_1[0x24];
      if (((int)(uVar14 * 2) < (int)uVar12) && ((int)uVar14 < (int)uVar12)) {
        pvVar4 = (void *)param_1[0x23];
        if ((int)uVar14 < 1) {
          free(pvVar4);
          uVar10 = param_1[0x25];
          piVar2 = (int *)0x0;
        }
        else if (pvVar4 == (void *)0x0) {
          piVar2 = malloc(uVar14 << 2);
          uVar10 = uVar14;
        }
        else {
          piVar2 = realloc(pvVar4,uVar14 << 2);
          uVar10 = param_1[0x25];
        }
        param_1[0x24] = uVar14;
        param_1[0x23] = (int)piVar2;
        uVar12 = uVar14;
        uVar14 = uVar10;
      }
      else {
        piVar2 = (int *)param_1[0x23];
      }
      goto LAB_00392c8c;
    }
LAB_00392e70:
    uVar12 = param_1[0x24];
    iVar3 = uVar14 + 1;
    uVar10 = uVar14 & (int)uVar14 >> 0x1f;
    if ((int)uVar12 < iVar3) goto LAB_00392e84;
  }
  piVar2 = piVar2 + uVar10;
  if (0 < (int)(uVar14 - uVar10)) {
    memmove(piVar2 + 1,piVar2,(uVar14 - uVar10) * 4);
  }
  *piVar2 = (int)param_2;
  if (param_2 != (int *)0x0) {
    piVar2 = param_2 + 0x1d;
    DataMemoryBarrier(0xf);
    do {
      bVar1 = (bool)hasExclusiveAccess(piVar2);
    } while (!bVar1);
    *piVar2 = *piVar2 + 1;
    DataMemoryBarrier(0xf);
  }
  pcVar7 = *(code **)(*param_1 + 0xc0);
  param_1[0x25] = param_1[0x25] + 1;
  (*pcVar7)(param_1);
  if (piVar9 != (int *)0x0) {
    piVar2 = piVar9 + 0x1d;
    DataMemoryBarrier(0xf);
    do {
      iVar3 = *piVar2;
      bVar1 = (bool)hasExclusiveAccess(piVar2);
    } while (!bVar1);
    *piVar2 = iVar3 + -1;
    DataMemoryBarrier(0xf);
    if (iVar3 + -1 == 0) {
      (**(code **)(*piVar9 + 4))(piVar9);
    }
  }
LAB_00392d4c:
  param_2[0x1e] = (int)param_1;
  return;
}

