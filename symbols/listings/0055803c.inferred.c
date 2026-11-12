/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

void FUN_0055803c(int param_1)

{
  void *pvVar1;
  int iVar2;
  uint uVar3;
  int iVar4;
  int iVar5;
  uint uVar6;
  int iVar7;
  uint uVar8;
  uint uVar9;
  
  iVar5 = 0x25;
  iVar2 = *(int *)(param_1 + 0xc);
  do {
    while( true ) {
      iVar4 = iVar5;
      iVar7 = iVar2 + 1;
      if ((iVar7 <= (int)*(uint *)(param_1 + 8)) ||
         (uVar3 = iVar7 + iVar7 / 2 + 8U & 0xfffffff8, *(uint *)(param_1 + 8) == uVar3)) break;
      pvVar1 = *(void **)(param_1 + 4);
      if ((int)uVar3 < 1) {
        free(pvVar1);
        iVar2 = *(int *)(param_1 + 0xc);
        pvVar1 = (void *)0x0;
        *(undefined4 *)(param_1 + 4) = 0;
        iVar7 = iVar2 + 1;
        *(uint *)(param_1 + 8) = uVar3;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar3 << 2);
          *(void **)(param_1 + 4) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar3 << 2);
          iVar2 = *(int *)(param_1 + 0xc);
          iVar7 = iVar2 + 1;
          *(void **)(param_1 + 4) = pvVar1;
        }
        *(uint *)(param_1 + 8) = uVar3;
      }
      *(int *)(param_1 + 0xc) = iVar7;
      if ((void *)((int)pvVar1 + iVar2 * 4) != (void *)0x0) {
        *(undefined4 *)((int)pvVar1 + iVar2 * 4) = 0;
      }
      iVar5 = iVar4 + -1;
      iVar2 = iVar7;
      if (iVar4 + -1 == 0) goto LAB_005580e4;
    }
    *(int *)(param_1 + 0xc) = iVar7;
    if (*(int *)(param_1 + 4) + iVar2 * 4 != 0) {
      *(undefined4 *)(*(int *)(param_1 + 4) + iVar2 * 4) = 0;
    }
    iVar5 = iVar4 + -1;
    iVar2 = iVar7;
  } while (iVar4 + -1 != 0);
LAB_005580e4:
  pvVar1 = (void *)(iVar4 + -1);
  iVar2 = *(int *)(param_1 + 0x18);
  uVar3 = *(uint *)(param_1 + 0x14);
  iVar5 = iVar2 + 1;
  if (((int)uVar3 < iVar5) && (uVar8 = iVar5 + iVar5 / 2 + 8U & 0xfffffff8, uVar3 != uVar8)) {
    if ((int)uVar8 < 1) {
      free(*(void **)(param_1 + 0x10));
      iVar2 = *(int *)(param_1 + 0x18);
      *(void **)(param_1 + 0x10) = pvVar1;
      iVar5 = iVar2 + 1;
    }
    else {
      if (*(void **)(param_1 + 0x10) == (void *)0x0) {
        pvVar1 = malloc(uVar8 << 2);
      }
      else {
        pvVar1 = realloc(*(void **)(param_1 + 0x10),uVar8 << 2);
        iVar2 = *(int *)(param_1 + 0x18);
        iVar5 = iVar2 + 1;
      }
      *(void **)(param_1 + 0x10) = pvVar1;
    }
    *(uint *)(param_1 + 0x14) = uVar8;
  }
  else {
    pvVar1 = *(void **)(param_1 + 0x10);
    uVar8 = uVar3;
  }
  iVar4 = iVar5 + 1;
  *(int *)(param_1 + 0x18) = iVar5;
  if ((void *)((int)pvVar1 + iVar2 * 4) != (void *)0x0) {
    *(undefined4 *)((int)pvVar1 + iVar2 * 4) = 0;
  }
  if (((int)uVar8 < iVar4) && (uVar3 = iVar4 + iVar4 / 2 + 8U & 0xfffffff8, uVar8 != uVar3)) {
    if ((int)uVar3 < 1) {
      free(*(void **)(param_1 + 0x10));
      iVar5 = *(int *)(param_1 + 0x18);
      pvVar1 = (void *)0x0;
      *(undefined4 *)(param_1 + 0x10) = 0;
      iVar4 = iVar5 + 1;
    }
    else {
      if (*(void **)(param_1 + 0x10) == (void *)0x0) {
        pvVar1 = malloc(uVar3 << 2);
      }
      else {
        pvVar1 = realloc(*(void **)(param_1 + 0x10),uVar3 << 2);
        iVar5 = *(int *)(param_1 + 0x18);
        iVar4 = iVar5 + 1;
      }
      *(void **)(param_1 + 0x10) = pvVar1;
    }
    *(uint *)(param_1 + 0x14) = uVar3;
  }
  else {
    pvVar1 = *(void **)(param_1 + 0x10);
    uVar3 = uVar8;
  }
  *(int *)(param_1 + 0x18) = iVar4;
  if ((void *)((int)pvVar1 + iVar5 * 4) != (void *)0x0) {
    *(undefined4 *)((int)pvVar1 + iVar5 * 4) = 0;
  }
  iVar5 = iVar4 + 1;
  if (((int)uVar3 < iVar5) && (uVar8 = iVar5 + iVar5 / 2 + 8U & 0xfffffff8, uVar3 != uVar8)) {
    pvVar1 = *(void **)(param_1 + 0x10);
    if ((int)uVar8 < 1) {
      free(pvVar1);
      iVar4 = *(int *)(param_1 + 0x18);
      pvVar1 = (void *)0x0;
      *(uint *)(param_1 + 0x14) = uVar8;
      *(undefined4 *)(param_1 + 0x10) = 0;
      iVar5 = iVar4 + 1;
    }
    else {
      if (pvVar1 == (void *)0x0) {
        pvVar1 = malloc(uVar8 << 2);
        *(void **)(param_1 + 0x10) = pvVar1;
      }
      else {
        pvVar1 = realloc(pvVar1,uVar8 << 2);
        iVar4 = *(int *)(param_1 + 0x18);
        iVar5 = iVar4 + 1;
        *(void **)(param_1 + 0x10) = pvVar1;
      }
      *(uint *)(param_1 + 0x14) = uVar8;
    }
  }
  else {
    pvVar1 = *(void **)(param_1 + 0x10);
  }
  *(int *)(param_1 + 0x18) = iVar5;
  if ((void *)((int)pvVar1 + iVar4 * 4) != (void *)0x0) {
    *(undefined4 *)((int)pvVar1 + iVar4 * 4) = 0;
  }
  iVar5 = *(int *)(param_1 + 0x24);
  uVar3 = *(uint *)(param_1 + 0x20);
  iVar2 = iVar5 + 1;
  if (((int)uVar3 < iVar2) && (uVar8 = iVar2 + iVar2 / 2 + 8U & 0xfffffff8, uVar3 != uVar8)) {
    if ((int)uVar8 < 1) {
      free(*(void **)(param_1 + 0x1c));
      iVar5 = *(int *)(param_1 + 0x24);
      pvVar1 = (void *)0x0;
      *(undefined4 *)(param_1 + 0x1c) = 0;
      iVar2 = iVar5 + 1;
    }
    else {
      if (*(void **)(param_1 + 0x1c) == (void *)0x0) {
        pvVar1 = malloc(uVar8 << 2);
      }
      else {
        pvVar1 = realloc(*(void **)(param_1 + 0x1c),uVar8 << 2);
        iVar5 = *(int *)(param_1 + 0x24);
        iVar2 = iVar5 + 1;
      }
      *(void **)(param_1 + 0x1c) = pvVar1;
    }
    *(uint *)(param_1 + 0x20) = uVar8;
  }
  else {
    pvVar1 = *(void **)(param_1 + 0x1c);
    uVar8 = uVar3;
  }
  *(int *)(param_1 + 0x24) = iVar2;
  if ((void *)((int)pvVar1 + iVar5 * 4) != (void *)0x0) {
    *(undefined4 *)((int)pvVar1 + iVar5 * 4) = 0;
  }
  iVar5 = iVar2 + 1;
  if (((int)uVar8 < iVar5) && (uVar3 = iVar5 + iVar5 / 2 + 8U & 0xfffffff8, uVar8 != uVar3)) {
    if ((int)uVar3 < 1) {
      free(*(void **)(param_1 + 0x1c));
      iVar2 = *(int *)(param_1 + 0x24);
      pvVar1 = (void *)0x0;
      *(undefined4 *)(param_1 + 0x1c) = 0;
      iVar5 = iVar2 + 1;
    }
    else {
      if (*(void **)(param_1 + 0x1c) == (void *)0x0) {
        pvVar1 = malloc(uVar3 << 2);
      }
      else {
        pvVar1 = realloc(*(void **)(param_1 + 0x1c),uVar3 << 2);
        iVar2 = *(int *)(param_1 + 0x24);
        iVar5 = iVar2 + 1;
      }
      *(void **)(param_1 + 0x1c) = pvVar1;
    }
    *(uint *)(param_1 + 0x20) = uVar3;
  }
  else {
    pvVar1 = *(void **)(param_1 + 0x1c);
    uVar3 = uVar8;
  }
  *(int *)(param_1 + 0x24) = iVar5;
  if ((void *)((int)pvVar1 + iVar2 * 4) != (void *)0x0) {
    *(undefined4 *)((int)pvVar1 + iVar2 * 4) = 0;
  }
  iVar2 = iVar5 + 1;
  if (((int)uVar3 < iVar2) && (uVar8 = iVar2 + iVar2 / 2 + 8U & 0xfffffff8, uVar3 != uVar8)) {
    if ((int)uVar8 < 1) {
      free(*(void **)(param_1 + 0x1c));
      iVar5 = *(int *)(param_1 + 0x24);
      pvVar1 = (void *)0x0;
      *(undefined4 *)(param_1 + 0x1c) = 0;
      iVar2 = iVar5 + 1;
    }
    else {
      if (*(void **)(param_1 + 0x1c) == (void *)0x0) {
        pvVar1 = malloc(uVar8 << 2);
      }
      else {
        pvVar1 = realloc(*(void **)(param_1 + 0x1c),uVar8 << 2);
        iVar5 = *(int *)(param_1 + 0x24);
        iVar2 = iVar5 + 1;
      }
      *(void **)(param_1 + 0x1c) = pvVar1;
    }
    *(uint *)(param_1 + 0x20) = uVar8;
  }
  else {
    pvVar1 = *(void **)(param_1 + 0x1c);
    uVar8 = uVar3;
  }
  *(int *)(param_1 + 0x24) = iVar2;
  if ((void *)((int)pvVar1 + iVar5 * 4) != (void *)0x0) {
    *(undefined4 *)((int)pvVar1 + iVar5 * 4) = 0;
  }
  iVar5 = iVar2 + 1;
  if (((int)uVar8 < iVar5) && (uVar3 = iVar5 + iVar5 / 2 + 8U & 0xfffffff8, uVar8 != uVar3)) {
    if ((int)uVar3 < 1) {
      free(*(void **)(param_1 + 0x1c));
      iVar2 = *(int *)(param_1 + 0x24);
      pvVar1 = (void *)0x0;
      *(undefined4 *)(param_1 + 0x1c) = 0;
      iVar5 = iVar2 + 1;
    }
    else {
      if (*(void **)(param_1 + 0x1c) == (void *)0x0) {
        pvVar1 = malloc(uVar3 << 2);
      }
      else {
        pvVar1 = realloc(*(void **)(param_1 + 0x1c),uVar3 << 2);
        iVar2 = *(int *)(param_1 + 0x24);
        iVar5 = iVar2 + 1;
      }
      *(void **)(param_1 + 0x1c) = pvVar1;
    }
    *(uint *)(param_1 + 0x20) = uVar3;
  }
  else {
    pvVar1 = *(void **)(param_1 + 0x1c);
    uVar3 = uVar8;
  }
  *(int *)(param_1 + 0x24) = iVar5;
  if ((void *)((int)pvVar1 + iVar2 * 4) != (void *)0x0) {
    *(undefined4 *)((int)pvVar1 + iVar2 * 4) = 0;
  }
  iVar2 = iVar5 + 1;
  if (((int)uVar3 < iVar2) && (uVar8 = iVar2 + iVar2 / 2 + 8U & 0xfffffff8, uVar3 != uVar8)) {
    if ((int)uVar8 < 1) {
      free(*(void **)(param_1 + 0x1c));
      iVar5 = *(int *)(param_1 + 0x24);
      pvVar1 = (void *)0x0;
      *(undefined4 *)(param_1 + 0x1c) = 0;
      iVar2 = iVar5 + 1;
    }
    else {
      if (*(void **)(param_1 + 0x1c) == (void *)0x0) {
        pvVar1 = malloc(uVar8 << 2);
      }
      else {
        pvVar1 = realloc(*(void **)(param_1 + 0x1c),uVar8 << 2);
        iVar5 = *(int *)(param_1 + 0x24);
        iVar2 = iVar5 + 1;
      }
      *(void **)(param_1 + 0x1c) = pvVar1;
    }
    *(uint *)(param_1 + 0x20) = uVar8;
  }
  else {
    pvVar1 = *(void **)(param_1 + 0x1c);
    uVar8 = uVar3;
  }
  *(int *)(param_1 + 0x24) = iVar2;
  if ((void *)((int)pvVar1 + iVar5 * 4) != (void *)0x0) {
    *(undefined4 *)((int)pvVar1 + iVar5 * 4) = 0;
  }
  iVar5 = iVar2 + 1;
  if (((int)uVar8 < iVar5) && (uVar3 = iVar5 + iVar5 / 2 + 8U & 0xfffffff8, uVar8 != uVar3)) {
    if ((int)uVar3 < 1) {
      free(*(void **)(param_1 + 0x1c));
      iVar2 = *(int *)(param_1 + 0x24);
      pvVar1 = (void *)0x0;
      *(undefined4 *)(param_1 + 0x1c) = 0;
      iVar5 = iVar2 + 1;
    }
    else {
      if (*(void **)(param_1 + 0x1c) == (void *)0x0) {
        pvVar1 = malloc(uVar3 << 2);
      }
      else {
        pvVar1 = realloc(*(void **)(param_1 + 0x1c),uVar3 << 2);
        iVar2 = *(int *)(param_1 + 0x24);
        iVar5 = iVar2 + 1;
      }
      *(void **)(param_1 + 0x1c) = pvVar1;
    }
    *(uint *)(param_1 + 0x20) = uVar3;
  }
  else {
    pvVar1 = *(void **)(param_1 + 0x1c);
    uVar3 = uVar8;
  }
  *(int *)(param_1 + 0x24) = iVar5;
  if ((void *)((int)pvVar1 + iVar2 * 4) != (void *)0x0) {
    *(undefined4 *)((int)pvVar1 + iVar2 * 4) = 0;
  }
  iVar2 = iVar5 + 1;
  if (((int)uVar3 < iVar2) && (uVar8 = iVar2 + iVar2 / 2 + 8U & 0xfffffff8, uVar3 != uVar8)) {
    pvVar1 = *(void **)(param_1 + 0x1c);
    if ((int)uVar8 < 1) {
      free(pvVar1);
      iVar5 = *(int *)(param_1 + 0x24);
      pvVar1 = (void *)0x0;
      *(uint *)(param_1 + 0x20) = uVar8;
      *(undefined4 *)(param_1 + 0x1c) = 0;
      iVar2 = iVar5 + 1;
    }
    else {
      if (pvVar1 == (void *)0x0) {
        pvVar1 = malloc(uVar8 << 2);
        *(void **)(param_1 + 0x1c) = pvVar1;
      }
      else {
        pvVar1 = realloc(pvVar1,uVar8 << 2);
        iVar5 = *(int *)(param_1 + 0x24);
        iVar2 = iVar5 + 1;
        *(void **)(param_1 + 0x1c) = pvVar1;
      }
      *(uint *)(param_1 + 0x20) = uVar8;
    }
  }
  else {
    pvVar1 = *(void **)(param_1 + 0x1c);
  }
  uVar3 = *(uint *)(param_1 + 0xc);
  *(int *)(param_1 + 0x24) = iVar2;
  if ((void *)((int)pvVar1 + iVar5 * 4) != (void *)0x0) {
    *(undefined4 *)((int)pvVar1 + iVar5 * 4) = 0;
  }
  if (uVar3 == 0) {
    if (*(int *)(param_1 + 8) < 1) {
      if (*(void **)(param_1 + 4) == (void *)0x0) {
        pvVar1 = malloc(0x20);
        iVar5 = 0;
      }
      else {
        pvVar1 = realloc(*(void **)(param_1 + 4),0x20);
        iVar5 = *(int *)(param_1 + 0xc);
      }
      *(void **)(param_1 + 4) = pvVar1;
      *(undefined4 *)(param_1 + 8) = 8;
    }
    else {
      pvVar1 = *(void **)(param_1 + 4);
      iVar5 = 0;
    }
    uVar3 = iVar5 + 1;
    *(uint *)(param_1 + 0xc) = uVar3;
    if ((void *)((int)pvVar1 + iVar5 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + iVar5 * 4) = param_1 + 0xac;
      pvVar1 = *(void **)(param_1 + 4);
    }
  }
  else {
    **(int **)(param_1 + 4) = param_1 + 0xac;
    pvVar1 = *(void **)(param_1 + 4);
  }
  if (uVar3 < 2) {
    uVar8 = uVar3 + 1;
    if (((int)*(uint *)(param_1 + 8) < (int)uVar8) &&
       (uVar9 = uVar8 + (int)uVar8 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 8) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar3 = *(uint *)(param_1 + 0xc);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 8) = uVar9;
        *(undefined4 *)(param_1 + 4) = 0;
        uVar8 = uVar3 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 4) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar3 = *(uint *)(param_1 + 0xc);
          uVar8 = uVar3 + 1;
          *(void **)(param_1 + 4) = pvVar1;
        }
        *(uint *)(param_1 + 8) = uVar9;
      }
    }
    *(uint *)(param_1 + 0xc) = uVar8;
    if ((void *)((int)pvVar1 + uVar3 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar3 * 4) = param_1 + 0xd4;
      pvVar1 = *(void **)(param_1 + 4);
    }
  }
  else {
    *(int *)((int)pvVar1 + 4) = param_1 + 0xd4;
    pvVar1 = *(void **)(param_1 + 4);
    uVar8 = uVar3;
  }
  if (uVar8 < 3) {
    uVar3 = uVar8 + 1;
    if (((int)*(uint *)(param_1 + 8) < (int)uVar3) &&
       (uVar9 = uVar3 + (int)uVar3 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 8) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar8 = *(uint *)(param_1 + 0xc);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 8) = uVar9;
        *(undefined4 *)(param_1 + 4) = 0;
        uVar3 = uVar8 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 4) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar8 = *(uint *)(param_1 + 0xc);
          uVar3 = uVar8 + 1;
          *(void **)(param_1 + 4) = pvVar1;
        }
        *(uint *)(param_1 + 8) = uVar9;
      }
    }
    *(uint *)(param_1 + 0xc) = uVar3;
    if ((void *)((int)pvVar1 + uVar8 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar8 * 4) = param_1 + 0xfc;
      pvVar1 = *(void **)(param_1 + 4);
    }
  }
  else {
    *(int *)((int)pvVar1 + 8) = param_1 + 0xfc;
    pvVar1 = *(void **)(param_1 + 4);
    uVar3 = uVar8;
  }
  if (uVar3 < 4) {
    uVar8 = uVar3 + 1;
    if (((int)*(uint *)(param_1 + 8) < (int)uVar8) &&
       (uVar9 = uVar8 + (int)uVar8 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 8) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar3 = *(uint *)(param_1 + 0xc);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 8) = uVar9;
        *(undefined4 *)(param_1 + 4) = 0;
        uVar8 = uVar3 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 4) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar3 = *(uint *)(param_1 + 0xc);
          uVar8 = uVar3 + 1;
          *(void **)(param_1 + 4) = pvVar1;
        }
        *(uint *)(param_1 + 8) = uVar9;
      }
    }
    *(uint *)(param_1 + 0xc) = uVar8;
    if ((void *)((int)pvVar1 + uVar3 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar3 * 4) = param_1 + 0x124;
      pvVar1 = *(void **)(param_1 + 4);
    }
  }
  else {
    *(int *)((int)pvVar1 + 0xc) = param_1 + 0x124;
    pvVar1 = *(void **)(param_1 + 4);
    uVar8 = uVar3;
  }
  if (uVar8 < 5) {
    uVar3 = uVar8 + 1;
    if (((int)*(uint *)(param_1 + 8) < (int)uVar3) &&
       (uVar9 = uVar3 + (int)uVar3 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 8) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar8 = *(uint *)(param_1 + 0xc);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 8) = uVar9;
        *(undefined4 *)(param_1 + 4) = 0;
        uVar3 = uVar8 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 4) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar8 = *(uint *)(param_1 + 0xc);
          uVar3 = uVar8 + 1;
          *(void **)(param_1 + 4) = pvVar1;
        }
        *(uint *)(param_1 + 8) = uVar9;
      }
    }
    *(uint *)(param_1 + 0xc) = uVar3;
    if ((void *)((int)pvVar1 + uVar8 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar8 * 4) = param_1 + 0x14c;
      pvVar1 = *(void **)(param_1 + 4);
    }
  }
  else {
    *(int *)((int)pvVar1 + 0x10) = param_1 + 0x14c;
    pvVar1 = *(void **)(param_1 + 4);
    uVar3 = uVar8;
  }
  if (uVar3 < 6) {
    uVar8 = uVar3 + 1;
    if (((int)*(uint *)(param_1 + 8) < (int)uVar8) &&
       (uVar9 = uVar8 + (int)uVar8 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 8) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar3 = *(uint *)(param_1 + 0xc);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 8) = uVar9;
        *(undefined4 *)(param_1 + 4) = 0;
        uVar8 = uVar3 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 4) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar3 = *(uint *)(param_1 + 0xc);
          uVar8 = uVar3 + 1;
          *(void **)(param_1 + 4) = pvVar1;
        }
        *(uint *)(param_1 + 8) = uVar9;
      }
    }
    *(uint *)(param_1 + 0xc) = uVar8;
    if ((void *)((int)pvVar1 + uVar3 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar3 * 4) = param_1 + 0x174;
      pvVar1 = *(void **)(param_1 + 4);
    }
  }
  else {
    *(int *)((int)pvVar1 + 0x14) = param_1 + 0x174;
    pvVar1 = *(void **)(param_1 + 4);
    uVar8 = uVar3;
  }
  if (uVar8 < 7) {
    uVar3 = uVar8 + 1;
    if (((int)*(uint *)(param_1 + 8) < (int)uVar3) &&
       (uVar9 = uVar3 + (int)uVar3 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 8) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar8 = *(uint *)(param_1 + 0xc);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 8) = uVar9;
        *(undefined4 *)(param_1 + 4) = 0;
        uVar3 = uVar8 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 4) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar8 = *(uint *)(param_1 + 0xc);
          uVar3 = uVar8 + 1;
          *(void **)(param_1 + 4) = pvVar1;
        }
        *(uint *)(param_1 + 8) = uVar9;
      }
    }
    *(uint *)(param_1 + 0xc) = uVar3;
    if ((void *)((int)pvVar1 + uVar8 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar8 * 4) = param_1 + 0x19c;
      pvVar1 = *(void **)(param_1 + 4);
    }
  }
  else {
    *(int *)((int)pvVar1 + 0x18) = param_1 + 0x19c;
    pvVar1 = *(void **)(param_1 + 4);
    uVar3 = uVar8;
  }
  if (uVar3 < 8) {
    uVar8 = uVar3 + 1;
    if (((int)*(uint *)(param_1 + 8) < (int)uVar8) &&
       (uVar9 = uVar8 + (int)uVar8 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 8) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar3 = *(uint *)(param_1 + 0xc);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 8) = uVar9;
        *(undefined4 *)(param_1 + 4) = 0;
        uVar8 = uVar3 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 4) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar3 = *(uint *)(param_1 + 0xc);
          uVar8 = uVar3 + 1;
          *(void **)(param_1 + 4) = pvVar1;
        }
        *(uint *)(param_1 + 8) = uVar9;
      }
    }
    *(uint *)(param_1 + 0xc) = uVar8;
    if ((void *)((int)pvVar1 + uVar3 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar3 * 4) = param_1 + 0x1c4;
      pvVar1 = *(void **)(param_1 + 4);
    }
  }
  else {
    *(int *)((int)pvVar1 + 0x1c) = param_1 + 0x1c4;
    pvVar1 = *(void **)(param_1 + 4);
    uVar8 = uVar3;
  }
  if (uVar8 < 9) {
    uVar3 = uVar8 + 1;
    if (((int)*(uint *)(param_1 + 8) < (int)uVar3) &&
       (uVar9 = uVar3 + (int)uVar3 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 8) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar8 = *(uint *)(param_1 + 0xc);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 8) = uVar9;
        *(undefined4 *)(param_1 + 4) = 0;
        uVar3 = uVar8 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 4) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar8 = *(uint *)(param_1 + 0xc);
          uVar3 = uVar8 + 1;
          *(void **)(param_1 + 4) = pvVar1;
        }
        *(uint *)(param_1 + 8) = uVar9;
      }
    }
    *(uint *)(param_1 + 0xc) = uVar3;
    if ((void *)((int)pvVar1 + uVar8 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar8 * 4) = param_1 + 0x1ec;
      pvVar1 = *(void **)(param_1 + 4);
    }
  }
  else {
    *(int *)((int)pvVar1 + 0x20) = param_1 + 0x1ec;
    pvVar1 = *(void **)(param_1 + 4);
    uVar3 = uVar8;
  }
  if (uVar3 < 10) {
    uVar8 = uVar3 + 1;
    if (((int)*(uint *)(param_1 + 8) < (int)uVar8) &&
       (uVar9 = uVar8 + (int)uVar8 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 8) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar3 = *(uint *)(param_1 + 0xc);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 8) = uVar9;
        *(undefined4 *)(param_1 + 4) = 0;
        uVar8 = uVar3 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 4) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar3 = *(uint *)(param_1 + 0xc);
          uVar8 = uVar3 + 1;
          *(void **)(param_1 + 4) = pvVar1;
        }
        *(uint *)(param_1 + 8) = uVar9;
      }
    }
    *(uint *)(param_1 + 0xc) = uVar8;
    if ((void *)((int)pvVar1 + uVar3 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar3 * 4) = param_1 + 0x214;
      pvVar1 = *(void **)(param_1 + 4);
    }
  }
  else {
    *(int *)((int)pvVar1 + 0x24) = param_1 + 0x214;
    pvVar1 = *(void **)(param_1 + 4);
    uVar8 = uVar3;
  }
  if (uVar8 < 0xb) {
    uVar3 = uVar8 + 1;
    if (((int)*(uint *)(param_1 + 8) < (int)uVar3) &&
       (uVar9 = uVar3 + (int)uVar3 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 8) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar8 = *(uint *)(param_1 + 0xc);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 8) = uVar9;
        *(undefined4 *)(param_1 + 4) = 0;
        uVar3 = uVar8 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 4) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar8 = *(uint *)(param_1 + 0xc);
          uVar3 = uVar8 + 1;
          *(void **)(param_1 + 4) = pvVar1;
        }
        *(uint *)(param_1 + 8) = uVar9;
      }
    }
    *(uint *)(param_1 + 0xc) = uVar3;
    if ((void *)((int)pvVar1 + uVar8 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar8 * 4) = param_1 + 0x23c;
      pvVar1 = *(void **)(param_1 + 4);
    }
  }
  else {
    *(int *)((int)pvVar1 + 0x28) = param_1 + 0x23c;
    pvVar1 = *(void **)(param_1 + 4);
    uVar3 = uVar8;
  }
  if (uVar3 < 0xc) {
    uVar8 = uVar3 + 1;
    if (((int)*(uint *)(param_1 + 8) < (int)uVar8) &&
       (uVar9 = uVar8 + (int)uVar8 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 8) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar3 = *(uint *)(param_1 + 0xc);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 8) = uVar9;
        *(undefined4 *)(param_1 + 4) = 0;
        uVar8 = uVar3 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 4) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar3 = *(uint *)(param_1 + 0xc);
          uVar8 = uVar3 + 1;
          *(void **)(param_1 + 4) = pvVar1;
        }
        *(uint *)(param_1 + 8) = uVar9;
      }
    }
    *(uint *)(param_1 + 0xc) = uVar8;
    if ((void *)((int)pvVar1 + uVar3 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar3 * 4) = param_1 + 0x264;
      pvVar1 = *(void **)(param_1 + 4);
    }
  }
  else {
    *(int *)((int)pvVar1 + 0x2c) = param_1 + 0x264;
    pvVar1 = *(void **)(param_1 + 4);
    uVar8 = uVar3;
  }
  if (uVar8 < 0xd) {
    uVar3 = uVar8 + 1;
    if (((int)*(uint *)(param_1 + 8) < (int)uVar3) &&
       (uVar9 = uVar3 + (int)uVar3 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 8) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar8 = *(uint *)(param_1 + 0xc);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 8) = uVar9;
        *(undefined4 *)(param_1 + 4) = 0;
        uVar3 = uVar8 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 4) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar8 = *(uint *)(param_1 + 0xc);
          uVar3 = uVar8 + 1;
          *(void **)(param_1 + 4) = pvVar1;
        }
        *(uint *)(param_1 + 8) = uVar9;
      }
    }
    *(uint *)(param_1 + 0xc) = uVar3;
    if ((void *)((int)pvVar1 + uVar8 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar8 * 4) = param_1 + 0x28c;
      pvVar1 = *(void **)(param_1 + 4);
    }
  }
  else {
    *(int *)((int)pvVar1 + 0x30) = param_1 + 0x28c;
    pvVar1 = *(void **)(param_1 + 4);
    uVar3 = uVar8;
  }
  if (uVar3 < 0xe) {
    uVar8 = uVar3 + 1;
    if (((int)*(uint *)(param_1 + 8) < (int)uVar8) &&
       (uVar9 = uVar8 + (int)uVar8 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 8) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar3 = *(uint *)(param_1 + 0xc);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 8) = uVar9;
        *(undefined4 *)(param_1 + 4) = 0;
        uVar8 = uVar3 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 4) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar3 = *(uint *)(param_1 + 0xc);
          uVar8 = uVar3 + 1;
          *(void **)(param_1 + 4) = pvVar1;
        }
        *(uint *)(param_1 + 8) = uVar9;
      }
    }
    *(uint *)(param_1 + 0xc) = uVar8;
    if ((void *)((int)pvVar1 + uVar3 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar3 * 4) = param_1 + 0x2b4;
      pvVar1 = *(void **)(param_1 + 4);
    }
  }
  else {
    *(int *)((int)pvVar1 + 0x34) = param_1 + 0x2b4;
    pvVar1 = *(void **)(param_1 + 4);
    uVar8 = uVar3;
  }
  if (uVar8 < 0xf) {
    uVar3 = uVar8 + 1;
    if (((int)*(uint *)(param_1 + 8) < (int)uVar3) &&
       (uVar9 = uVar3 + (int)uVar3 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 8) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar8 = *(uint *)(param_1 + 0xc);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 8) = uVar9;
        *(undefined4 *)(param_1 + 4) = 0;
        uVar3 = uVar8 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 4) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar8 = *(uint *)(param_1 + 0xc);
          uVar3 = uVar8 + 1;
          *(void **)(param_1 + 4) = pvVar1;
        }
        *(uint *)(param_1 + 8) = uVar9;
      }
    }
    *(uint *)(param_1 + 0xc) = uVar3;
    if ((void *)((int)pvVar1 + uVar8 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar8 * 4) = param_1 + 0x2dc;
      pvVar1 = *(void **)(param_1 + 4);
    }
  }
  else {
    *(int *)((int)pvVar1 + 0x38) = param_1 + 0x2dc;
    pvVar1 = *(void **)(param_1 + 4);
    uVar3 = uVar8;
  }
  if (uVar3 < 0x10) {
    uVar8 = uVar3 + 1;
    if (((int)*(uint *)(param_1 + 8) < (int)uVar8) &&
       (uVar9 = uVar8 + (int)uVar8 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 8) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar3 = *(uint *)(param_1 + 0xc);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 8) = uVar9;
        *(undefined4 *)(param_1 + 4) = 0;
        uVar8 = uVar3 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 4) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar3 = *(uint *)(param_1 + 0xc);
          uVar8 = uVar3 + 1;
          *(void **)(param_1 + 4) = pvVar1;
        }
        *(uint *)(param_1 + 8) = uVar9;
      }
    }
    *(uint *)(param_1 + 0xc) = uVar8;
    if ((void *)((int)pvVar1 + uVar3 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar3 * 4) = param_1 + 0x304;
      pvVar1 = *(void **)(param_1 + 4);
    }
  }
  else {
    *(int *)((int)pvVar1 + 0x3c) = param_1 + 0x304;
    pvVar1 = *(void **)(param_1 + 4);
    uVar8 = uVar3;
  }
  if (uVar8 < 0x11) {
    uVar3 = uVar8 + 1;
    if (((int)*(uint *)(param_1 + 8) < (int)uVar3) &&
       (uVar9 = uVar3 + (int)uVar3 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 8) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar8 = *(uint *)(param_1 + 0xc);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 8) = uVar9;
        *(undefined4 *)(param_1 + 4) = 0;
        uVar3 = uVar8 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 4) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar8 = *(uint *)(param_1 + 0xc);
          uVar3 = uVar8 + 1;
          *(void **)(param_1 + 4) = pvVar1;
        }
        *(uint *)(param_1 + 8) = uVar9;
      }
    }
    *(uint *)(param_1 + 0xc) = uVar3;
    if ((void *)((int)pvVar1 + uVar8 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar8 * 4) = param_1 + 0x32c;
      pvVar1 = *(void **)(param_1 + 4);
    }
  }
  else {
    *(int *)((int)pvVar1 + 0x40) = param_1 + 0x32c;
    pvVar1 = *(void **)(param_1 + 4);
    uVar3 = uVar8;
  }
  if (uVar3 < 0x12) {
    uVar8 = uVar3 + 1;
    if (((int)*(uint *)(param_1 + 8) < (int)uVar8) &&
       (uVar9 = uVar8 + (int)uVar8 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 8) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar3 = *(uint *)(param_1 + 0xc);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 8) = uVar9;
        *(undefined4 *)(param_1 + 4) = 0;
        uVar8 = uVar3 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 4) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar3 = *(uint *)(param_1 + 0xc);
          uVar8 = uVar3 + 1;
          *(void **)(param_1 + 4) = pvVar1;
        }
        *(uint *)(param_1 + 8) = uVar9;
      }
    }
    *(uint *)(param_1 + 0xc) = uVar8;
    if ((void *)((int)pvVar1 + uVar3 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar3 * 4) = param_1 + 0x354;
      pvVar1 = *(void **)(param_1 + 4);
    }
  }
  else {
    *(int *)((int)pvVar1 + 0x44) = param_1 + 0x354;
    pvVar1 = *(void **)(param_1 + 4);
    uVar8 = uVar3;
  }
  if (uVar8 < 0x13) {
    uVar3 = uVar8 + 1;
    if (((int)*(uint *)(param_1 + 8) < (int)uVar3) &&
       (uVar9 = uVar3 + (int)uVar3 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 8) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar8 = *(uint *)(param_1 + 0xc);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 8) = uVar9;
        *(undefined4 *)(param_1 + 4) = 0;
        uVar3 = uVar8 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 4) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar8 = *(uint *)(param_1 + 0xc);
          uVar3 = uVar8 + 1;
          *(void **)(param_1 + 4) = pvVar1;
        }
        *(uint *)(param_1 + 8) = uVar9;
      }
    }
    *(uint *)(param_1 + 0xc) = uVar3;
    if ((void *)((int)pvVar1 + uVar8 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar8 * 4) = param_1 + 0x37c;
      pvVar1 = *(void **)(param_1 + 4);
    }
  }
  else {
    *(int *)((int)pvVar1 + 0x48) = param_1 + 0x37c;
    pvVar1 = *(void **)(param_1 + 4);
    uVar3 = uVar8;
  }
  if (uVar3 < 0x14) {
    uVar8 = uVar3 + 1;
    if (((int)*(uint *)(param_1 + 8) < (int)uVar8) &&
       (uVar9 = uVar8 + (int)uVar8 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 8) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar3 = *(uint *)(param_1 + 0xc);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 8) = uVar9;
        *(undefined4 *)(param_1 + 4) = 0;
        uVar8 = uVar3 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 4) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar3 = *(uint *)(param_1 + 0xc);
          uVar8 = uVar3 + 1;
          *(void **)(param_1 + 4) = pvVar1;
        }
        *(uint *)(param_1 + 8) = uVar9;
      }
    }
    *(uint *)(param_1 + 0xc) = uVar8;
    if ((void *)((int)pvVar1 + uVar3 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar3 * 4) = param_1 + 0x3a4;
      pvVar1 = *(void **)(param_1 + 4);
    }
  }
  else {
    *(int *)((int)pvVar1 + 0x4c) = param_1 + 0x3a4;
    pvVar1 = *(void **)(param_1 + 4);
    uVar8 = uVar3;
  }
  if (uVar8 < 0x15) {
    uVar3 = uVar8 + 1;
    if (((int)*(uint *)(param_1 + 8) < (int)uVar3) &&
       (uVar9 = uVar3 + (int)uVar3 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 8) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar8 = *(uint *)(param_1 + 0xc);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 8) = uVar9;
        *(undefined4 *)(param_1 + 4) = 0;
        uVar3 = uVar8 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 4) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar8 = *(uint *)(param_1 + 0xc);
          uVar3 = uVar8 + 1;
          *(void **)(param_1 + 4) = pvVar1;
        }
        *(uint *)(param_1 + 8) = uVar9;
      }
    }
    *(uint *)(param_1 + 0xc) = uVar3;
    if ((void *)((int)pvVar1 + uVar8 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar8 * 4) = param_1 + 0x3cc;
      pvVar1 = *(void **)(param_1 + 4);
    }
  }
  else {
    *(int *)((int)pvVar1 + 0x50) = param_1 + 0x3cc;
    pvVar1 = *(void **)(param_1 + 4);
    uVar3 = uVar8;
  }
  uVar8 = 0x15;
  while( true ) {
    iVar5 = param_1 + 0x3f4 + (uVar8 - 0x15) * 0x28;
    if (uVar8 < uVar3) {
      *(int *)((int)pvVar1 + uVar8 * 4) = iVar5;
      uVar9 = uVar3;
    }
    else {
      uVar9 = uVar3 + 1;
      if (((int)*(uint *)(param_1 + 8) < (int)uVar9) &&
         (uVar6 = uVar9 + (int)uVar9 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 8) != uVar6)) {
        if ((int)uVar6 < 1) {
          free(pvVar1);
          uVar3 = *(uint *)(param_1 + 0xc);
          pvVar1 = (void *)0x0;
          *(undefined4 *)(param_1 + 4) = 0;
          uVar9 = uVar3 + 1;
          *(uint *)(param_1 + 8) = uVar6;
        }
        else {
          if (pvVar1 == (void *)0x0) {
            pvVar1 = malloc(uVar6 << 2);
            *(void **)(param_1 + 4) = pvVar1;
          }
          else {
            pvVar1 = realloc(pvVar1,uVar6 << 2);
            uVar3 = *(uint *)(param_1 + 0xc);
            uVar9 = uVar3 + 1;
            *(void **)(param_1 + 4) = pvVar1;
          }
          *(uint *)(param_1 + 8) = uVar6;
        }
      }
      *(uint *)(param_1 + 0xc) = uVar9;
      if ((void *)((int)pvVar1 + uVar3 * 4) != (void *)0x0) {
        *(int *)((int)pvVar1 + uVar3 * 4) = iVar5;
      }
    }
    uVar8 = uVar8 + 1;
    if (uVar8 == 0x25) break;
    pvVar1 = *(void **)(param_1 + 4);
    uVar3 = uVar9;
  }
  uVar3 = *(uint *)(param_1 + 0x18);
  if (uVar3 == 0) {
    if (*(int *)(param_1 + 0x14) < 1) {
      if (*(void **)(param_1 + 0x10) == (void *)0x0) {
        pvVar1 = malloc(0x20);
        iVar5 = 0;
      }
      else {
        pvVar1 = realloc(*(void **)(param_1 + 0x10),0x20);
        iVar5 = *(int *)(param_1 + 0x18);
      }
      *(void **)(param_1 + 0x10) = pvVar1;
      *(undefined4 *)(param_1 + 0x14) = 8;
    }
    else {
      pvVar1 = *(void **)(param_1 + 0x10);
      iVar5 = 0;
    }
    uVar3 = iVar5 + 1;
    *(uint *)(param_1 + 0x18) = uVar3;
    if ((void *)((int)pvVar1 + iVar5 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + iVar5 * 4) = param_1 + 0x674;
      pvVar1 = *(void **)(param_1 + 0x10);
    }
  }
  else {
    **(int **)(param_1 + 0x10) = param_1 + 0x674;
    pvVar1 = *(void **)(param_1 + 0x10);
  }
  if (uVar3 < 2) {
    uVar8 = uVar3 + 1;
    if (((int)*(uint *)(param_1 + 0x14) < (int)uVar8) &&
       (uVar9 = uVar8 + (int)uVar8 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 0x14) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar3 = *(uint *)(param_1 + 0x18);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 0x14) = uVar9;
        *(undefined4 *)(param_1 + 0x10) = 0;
        uVar8 = uVar3 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 0x10) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar3 = *(uint *)(param_1 + 0x18);
          uVar8 = uVar3 + 1;
          *(void **)(param_1 + 0x10) = pvVar1;
        }
        *(uint *)(param_1 + 0x14) = uVar9;
      }
    }
    *(uint *)(param_1 + 0x18) = uVar8;
    if ((void *)((int)pvVar1 + uVar3 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar3 * 4) = param_1 + 0x69c;
      pvVar1 = *(void **)(param_1 + 0x10);
    }
  }
  else {
    *(int *)((int)pvVar1 + 4) = param_1 + 0x69c;
    pvVar1 = *(void **)(param_1 + 0x10);
    uVar8 = uVar3;
  }
  if (uVar8 < 3) {
    iVar5 = uVar8 + 1;
    if (((int)*(uint *)(param_1 + 0x14) < iVar5) &&
       (uVar3 = iVar5 + iVar5 / 2 + 8U & 0xfffffff8, *(uint *)(param_1 + 0x14) != uVar3)) {
      if ((int)uVar3 < 1) {
        free(pvVar1);
        uVar8 = *(uint *)(param_1 + 0x18);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 0x14) = uVar3;
        *(undefined4 *)(param_1 + 0x10) = 0;
        iVar5 = uVar8 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar3 << 2);
          *(void **)(param_1 + 0x10) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar3 << 2);
          uVar8 = *(uint *)(param_1 + 0x18);
          iVar5 = uVar8 + 1;
          *(void **)(param_1 + 0x10) = pvVar1;
        }
        *(uint *)(param_1 + 0x14) = uVar3;
      }
    }
    *(int *)(param_1 + 0x18) = iVar5;
    if ((void *)((int)pvVar1 + uVar8 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar8 * 4) = param_1 + 0x6c4;
    }
  }
  else {
    *(int *)((int)pvVar1 + 8) = param_1 + 0x6c4;
  }
  uVar3 = *(uint *)(param_1 + 0x24);
  if (uVar3 == 0) {
    if (*(int *)(param_1 + 0x20) < 1) {
      if (*(void **)(param_1 + 0x1c) == (void *)0x0) {
        pvVar1 = malloc(0x20);
        iVar5 = 0;
      }
      else {
        pvVar1 = realloc(*(void **)(param_1 + 0x1c),0x20);
        iVar5 = *(int *)(param_1 + 0x24);
      }
      *(void **)(param_1 + 0x1c) = pvVar1;
      *(undefined4 *)(param_1 + 0x20) = 8;
    }
    else {
      pvVar1 = *(void **)(param_1 + 0x1c);
      iVar5 = 0;
    }
    uVar3 = iVar5 + 1;
    *(uint *)(param_1 + 0x24) = uVar3;
    if ((void *)((int)pvVar1 + iVar5 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + iVar5 * 4) = param_1 + 0xcf4;
      pvVar1 = *(void **)(param_1 + 0x1c);
    }
  }
  else {
    **(int **)(param_1 + 0x1c) = param_1 + 0xcf4;
    pvVar1 = *(void **)(param_1 + 0x1c);
  }
  if (uVar3 < 2) {
    uVar8 = uVar3 + 1;
    if (((int)*(uint *)(param_1 + 0x20) < (int)uVar8) &&
       (uVar9 = uVar8 + (int)uVar8 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 0x20) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar3 = *(uint *)(param_1 + 0x24);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 0x20) = uVar9;
        *(undefined4 *)(param_1 + 0x1c) = 0;
        uVar8 = uVar3 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 0x1c) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar3 = *(uint *)(param_1 + 0x24);
          uVar8 = uVar3 + 1;
          *(void **)(param_1 + 0x1c) = pvVar1;
        }
        *(uint *)(param_1 + 0x20) = uVar9;
      }
    }
    *(uint *)(param_1 + 0x24) = uVar8;
    if ((void *)((int)pvVar1 + uVar3 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar3 * 4) = param_1 + 0xd5c;
    }
  }
  else {
    *(int *)((int)pvVar1 + 4) = param_1 + 0xd5c;
    uVar8 = uVar3;
  }
  pvVar1 = *(void **)(param_1 + 0x1c);
  if (uVar8 < 3) {
    uVar3 = uVar8 + 1;
    if (((int)*(uint *)(param_1 + 0x20) < (int)uVar3) &&
       (uVar9 = uVar3 + (int)uVar3 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 0x20) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar8 = *(uint *)(param_1 + 0x24);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 0x20) = uVar9;
        *(undefined4 *)(param_1 + 0x1c) = 0;
        uVar3 = uVar8 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 0x1c) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar8 = *(uint *)(param_1 + 0x24);
          uVar3 = uVar8 + 1;
          *(void **)(param_1 + 0x1c) = pvVar1;
        }
        *(uint *)(param_1 + 0x20) = uVar9;
      }
    }
    *(uint *)(param_1 + 0x24) = uVar3;
    if ((void *)((int)pvVar1 + uVar8 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar8 * 4) = param_1 + 0xdc4;
    }
  }
  else {
    *(int *)((int)pvVar1 + 8) = param_1 + 0xdc4;
    uVar3 = uVar8;
  }
  pvVar1 = *(void **)(param_1 + 0x1c);
  if (uVar3 < 4) {
    uVar8 = uVar3 + 1;
    if (((int)*(uint *)(param_1 + 0x20) < (int)uVar8) &&
       (uVar9 = uVar8 + (int)uVar8 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 0x20) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar3 = *(uint *)(param_1 + 0x24);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 0x20) = uVar9;
        *(undefined4 *)(param_1 + 0x1c) = 0;
        uVar8 = uVar3 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 0x1c) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar3 = *(uint *)(param_1 + 0x24);
          uVar8 = uVar3 + 1;
          *(void **)(param_1 + 0x1c) = pvVar1;
        }
        *(uint *)(param_1 + 0x20) = uVar9;
      }
    }
    *(uint *)(param_1 + 0x24) = uVar8;
    if ((void *)((int)pvVar1 + uVar3 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar3 * 4) = param_1 + 0xe2c;
    }
  }
  else {
    *(int *)((int)pvVar1 + 0xc) = param_1 + 0xe2c;
    uVar8 = uVar3;
  }
  pvVar1 = *(void **)(param_1 + 0x1c);
  if (uVar8 < 5) {
    uVar3 = uVar8 + 1;
    if (((int)*(uint *)(param_1 + 0x20) < (int)uVar3) &&
       (uVar9 = uVar3 + (int)uVar3 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 0x20) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar8 = *(uint *)(param_1 + 0x24);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 0x20) = uVar9;
        *(undefined4 *)(param_1 + 0x1c) = 0;
        uVar3 = uVar8 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 0x1c) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar8 = *(uint *)(param_1 + 0x24);
          uVar3 = uVar8 + 1;
          *(void **)(param_1 + 0x1c) = pvVar1;
        }
        *(uint *)(param_1 + 0x20) = uVar9;
      }
    }
    *(uint *)(param_1 + 0x24) = uVar3;
    if ((void *)((int)pvVar1 + uVar8 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar8 * 4) = param_1 + 0xe94;
    }
  }
  else {
    *(int *)((int)pvVar1 + 0x10) = param_1 + 0xe94;
    uVar3 = uVar8;
  }
  pvVar1 = *(void **)(param_1 + 0x1c);
  if (uVar3 < 6) {
    uVar8 = uVar3 + 1;
    if (((int)*(uint *)(param_1 + 0x20) < (int)uVar8) &&
       (uVar9 = uVar8 + (int)uVar8 / 2 + 8 & 0xfffffff8, *(uint *)(param_1 + 0x20) != uVar9)) {
      if ((int)uVar9 < 1) {
        free(pvVar1);
        uVar3 = *(uint *)(param_1 + 0x24);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 0x20) = uVar9;
        *(undefined4 *)(param_1 + 0x1c) = 0;
        uVar8 = uVar3 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar9 << 2);
          *(void **)(param_1 + 0x1c) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar9 << 2);
          uVar3 = *(uint *)(param_1 + 0x24);
          uVar8 = uVar3 + 1;
          *(void **)(param_1 + 0x1c) = pvVar1;
        }
        *(uint *)(param_1 + 0x20) = uVar9;
      }
    }
    *(uint *)(param_1 + 0x24) = uVar8;
    if ((void *)((int)pvVar1 + uVar3 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar3 * 4) = param_1 + 0xefc;
    }
  }
  else {
    *(int *)((int)pvVar1 + 0x14) = param_1 + 0xefc;
    uVar8 = uVar3;
  }
  pvVar1 = *(void **)(param_1 + 0x1c);
  iVar5 = param_1 + 0xf64;
  if (uVar8 < 7) {
    iVar2 = uVar8 + 1;
    if (((int)*(uint *)(param_1 + 0x20) < iVar2) &&
       (uVar3 = iVar2 + iVar2 / 2 + 8U & 0xfffffff8, *(uint *)(param_1 + 0x20) != uVar3)) {
      if ((int)uVar3 < 1) {
        free(pvVar1);
        uVar8 = *(uint *)(param_1 + 0x24);
        pvVar1 = (void *)0x0;
        *(uint *)(param_1 + 0x20) = uVar3;
        *(undefined4 *)(param_1 + 0x1c) = 0;
        iVar2 = uVar8 + 1;
      }
      else {
        if (pvVar1 == (void *)0x0) {
          pvVar1 = malloc(uVar3 << 2);
          *(void **)(param_1 + 0x1c) = pvVar1;
        }
        else {
          pvVar1 = realloc(pvVar1,uVar3 << 2);
          uVar8 = *(uint *)(param_1 + 0x24);
          iVar2 = uVar8 + 1;
          *(void **)(param_1 + 0x1c) = pvVar1;
        }
        *(uint *)(param_1 + 0x20) = uVar3;
      }
      *(int *)(param_1 + 0x24) = iVar2;
      if ((void *)((int)pvVar1 + uVar8 * 4) != (void *)0x0) {
        *(int *)((int)pvVar1 + uVar8 * 4) = iVar5;
      }
      return;
    }
    *(int *)(param_1 + 0x24) = iVar2;
    if ((void *)((int)pvVar1 + uVar8 * 4) != (void *)0x0) {
      *(int *)((int)pvVar1 + uVar8 * 4) = iVar5;
    }
    return;
  }
  *(int *)((int)pvVar1 + 0x18) = iVar5;
  return;
}

