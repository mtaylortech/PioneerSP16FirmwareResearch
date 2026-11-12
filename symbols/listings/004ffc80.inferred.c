/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_004ffc80(int *param_1,int *param_2)

{
  bool bVar1;
  int iVar2;
  undefined4 uVar3;
  void *pvVar4;
  int iVar5;
  int iVar6;
  int iVar7;
  void *pvVar8;
  int iVar9;
  uint uVar10;
  int iVar11;
  int iVar12;
  int iVar13;
  int iVar14;
  int iVar15;
  int iVar16;
  int iVar17;
  undefined4 uVar18;
  undefined4 uVar19;
  int *piVar20;
  int iVar21;
  undefined4 uVar22;
  undefined4 local_68;
  int *local_38;
  undefined4 local_34;
  int local_30;
  
  if (param_2[2] < 1) {
    return;
  }
  if (param_2[3] < 1) {
    return;
  }
  if (param_1[2] == 0) {
    if (param_1[1] < 1) {
      if ((void *)*param_1 == (void *)0x0) {
        pvVar4 = malloc(0x80);
        iVar9 = 0;
      }
      else {
        pvVar4 = realloc((void *)*param_1,0x80);
        iVar9 = param_1[2];
      }
      *param_1 = (int)pvVar4;
      param_1[1] = 8;
    }
    else {
      pvVar4 = (void *)*param_1;
      iVar9 = 0;
    }
    pvVar8 = (void *)((int)pvVar4 + iVar9 * 0x10);
    param_1[2] = iVar9 + 1;
  }
  else {
    uVar10 = param_1[2] - 1;
    bVar1 = false;
    iVar9 = uVar10 * 0x10;
    while (-1 < (int)uVar10) {
      iVar6 = *param_2;
      iVar2 = param_2[2];
      piVar20 = (int *)(*param_1 + iVar9);
      iVar7 = *(int *)(*param_1 + iVar9);
      iVar5 = iVar6 + iVar2;
      if (iVar7 < iVar5) {
        iVar11 = param_2[1];
        iVar21 = param_2[3];
        iVar13 = piVar20[1];
        iVar16 = iVar11 + iVar21;
        if (iVar16 <= iVar13) goto LAB_004ffe5c;
        iVar12 = piVar20[2];
        iVar14 = iVar7 + iVar12;
        if (iVar14 <= iVar6) goto LAB_004ffe5c;
        iVar17 = piVar20[3];
        iVar15 = iVar13 + iVar17;
        if ((((iVar15 <= iVar11) || (iVar2 < 1)) || (iVar21 < 1)) || ((iVar12 < 1 || (iVar17 < 1))))
        goto LAB_004ffe5c;
        if (iVar7 < iVar6) {
          if (iVar13 < iVar11) {
            local_68 = 0xc;
            uVar22 = 8;
            uVar3 = 0;
            uVar18 = 4;
          }
          else {
            local_68 = 0xe;
            uVar22 = 10;
            uVar3 = 2;
            uVar18 = 6;
          }
LAB_004ffda0:
          if (iVar14 < iVar5) {
            uVar22 = local_68;
            uVar3 = uVar18;
          }
          if (iVar15 < iVar16) {
            uVar3 = uVar22;
          }
          switch(uVar3) {
          case 7:
            piVar20[1] = iVar16;
            piVar20[3] = iVar15 - iVar16;
            iVar9 = iVar9 + -0x10;
            uVar10 = uVar10 - 1;
            break;
          default:
            bVar1 = true;
            goto LAB_004ffe5c;
          case 0xb:
            iVar9 = iVar9 + -0x10;
            *piVar20 = iVar5;
            uVar10 = uVar10 - 1;
            piVar20[2] = iVar14 - iVar5;
            break;
          case 0xd:
            iVar9 = iVar9 + -0x10;
            uVar10 = uVar10 - 1;
            piVar20[3] = iVar11 - iVar13;
            break;
          case 0xe:
            iVar9 = iVar9 + -0x10;
            piVar20[2] = iVar6 - iVar7;
            uVar10 = uVar10 - 1;
          }
        }
        else {
          if (iVar13 < iVar11) {
            uVar18 = 5;
            local_68 = 0xd;
            uVar3 = 1;
            uVar22 = 9;
            goto LAB_004ffda0;
          }
          if (iVar5 < iVar14) {
            uVar22 = 0xb;
            local_68 = 0xf;
            uVar18 = 7;
            uVar3 = 3;
            goto LAB_004ffda0;
          }
          if (iVar16 < iVar15) {
            uVar22 = 0xb;
            local_68 = 0xf;
            uVar18 = 7;
            uVar3 = 3;
            goto LAB_004ffda0;
          }
          if (((iVar6 == iVar7) && (iVar11 == iVar13)) && ((iVar2 == iVar12 && (iVar21 == iVar17))))
          {
            return;
          }
          if ((uint)param_1[2] <= uVar10) goto LAB_004ffe5c;
          iVar2 = param_1[2] - 1;
          param_1[2] = iVar2;
          if (0 < (int)(iVar2 - uVar10)) {
            memmove(piVar20,piVar20 + 4,(iVar2 - uVar10) * 0x10);
            iVar2 = param_1[2];
          }
          if (param_1[1] <= (iVar2 << 1 & ~((iVar2 << 1) >> 0x1f))) goto LAB_004ffe5c;
          if (iVar2 < 4) {
            iVar2 = 4;
          }
          if (param_1[1] <= iVar2) goto LAB_004ffe5c;
          if ((void *)*param_1 == (void *)0x0) {
            pvVar4 = malloc(iVar2 << 4);
            *param_1 = (int)pvVar4;
            param_1[1] = iVar2;
          }
          else {
            pvVar4 = realloc((void *)*param_1,iVar2 << 4);
            *param_1 = (int)pvVar4;
            param_1[1] = iVar2;
          }
          iVar9 = iVar9 + -0x10;
          uVar10 = uVar10 - 1;
        }
      }
      else {
LAB_004ffe5c:
        iVar9 = iVar9 + -0x10;
        uVar10 = uVar10 - 1;
      }
    }
    iVar9 = param_1[2];
    if ((bVar1) && (0 < iVar9)) {
      iVar2 = param_2[2];
      local_38 = (int *)0x0;
      local_34 = 0;
      local_30 = 0;
      if ((0 < iVar2) && (iVar5 = param_2[3], 0 < iVar5)) {
        local_38 = malloc(0x80);
        local_34 = 8;
        local_30 = 1;
        if (local_38 == (int *)0x0) {
          iVar9 = param_1[2];
        }
        else {
          iVar6 = param_2[1];
          iVar9 = param_1[2];
          *local_38 = *param_2;
          local_38[1] = iVar6;
          *(ulonglong *)(local_38 + 2) = CONCAT44(iVar5,iVar2);
        }
      }
      iVar9 = iVar9 + -1;
      iVar2 = iVar9 * 0x10;
      do {
        if (iVar9 < 0) {
          iVar9 = 0;
          piVar20 = local_38;
          iVar2 = local_30;
          while (iVar2 = iVar2 + -1, -1 < iVar2) {
            iVar6 = param_1[2];
            iVar5 = iVar6 + 1;
            uVar18 = *(undefined4 *)((int)piVar20 + iVar9);
            uVar19 = *(undefined4 *)((int)piVar20 + iVar9 + 4);
            uVar22 = *(undefined4 *)((int)piVar20 + iVar9 + 8);
            uVar3 = *(undefined4 *)((int)piVar20 + iVar9 + 0xc);
            if ((param_1[1] < iVar5) &&
               (uVar10 = iVar5 + iVar5 / 2 + 8U & 0xfffffff8, param_1[1] != uVar10)) {
              pvVar4 = (void *)*param_1;
              if ((int)uVar10 < 1) {
                free(pvVar4);
                pvVar4 = (void *)0x0;
                iVar6 = param_1[2];
                iVar5 = iVar6 + 1;
                *param_1 = 0;
                param_1[1] = uVar10;
                piVar20 = local_38;
              }
              else {
                if (pvVar4 == (void *)0x0) {
                  pvVar4 = malloc(uVar10 << 4);
                  *param_1 = (int)pvVar4;
                }
                else {
                  pvVar4 = realloc(pvVar4,uVar10 << 4);
                  iVar6 = param_1[2];
                  iVar5 = iVar6 + 1;
                  *param_1 = (int)pvVar4;
                  piVar20 = local_38;
                }
                param_1[1] = uVar10;
              }
            }
            else {
              pvVar4 = (void *)*param_1;
            }
            pvVar8 = (void *)((int)pvVar4 + iVar6 * 0x10);
            param_1[2] = iVar5;
            if (pvVar8 != (void *)0x0) {
              *(undefined4 *)((int)pvVar4 + iVar6 * 0x10) = uVar18;
              *(undefined4 *)((int)pvVar8 + 4) = uVar19;
              *(undefined4 *)((int)pvVar8 + 8) = uVar22;
              *(undefined4 *)((int)pvVar8 + 0xc) = uVar3;
            }
            iVar9 = iVar9 + 0x10;
          }
          free(piVar20);
          return;
        }
        iVar5 = *param_1 + iVar2;
        iVar6 = *(int *)(*param_1 + iVar2);
        if (iVar6 < *param_2 + param_2[2]) {
          if (((((*(int *)(iVar5 + 4) < param_2[1] + param_2[3]) &&
                (*param_2 < iVar6 + *(int *)(iVar5 + 8))) &&
               (param_2[1] < *(int *)(iVar5 + 4) + *(int *)(iVar5 + 0xc))) &&
              ((0 < param_2[2] && (0 < param_2[3])))) &&
             ((0 < *(int *)(iVar5 + 8) &&
              ((0 < *(int *)(iVar5 + 0xc) && (FUN_004ff798(&local_38), local_30 == 0)))))) {
            free(local_38);
            return;
          }
        }
        iVar9 = iVar9 + -1;
        iVar2 = iVar2 + -0x10;
      } while( true );
    }
    iVar2 = iVar9 + 1;
    if ((param_1[1] < iVar2) && (uVar10 = iVar2 + iVar2 / 2 + 8U & 0xfffffff8, param_1[1] != uVar10)
       ) {
      pvVar4 = (void *)*param_1;
      if ((int)uVar10 < 1) {
        free(pvVar4);
        iVar9 = param_1[2];
        pvVar4 = (void *)0x0;
        param_1[1] = uVar10;
        *param_1 = 0;
        iVar2 = iVar9 + 1;
      }
      else {
        if (pvVar4 == (void *)0x0) {
          pvVar4 = malloc(uVar10 << 4);
          *param_1 = (int)pvVar4;
        }
        else {
          pvVar4 = realloc(pvVar4,uVar10 << 4);
          iVar9 = param_1[2];
          iVar2 = iVar9 + 1;
          *param_1 = (int)pvVar4;
        }
        param_1[1] = uVar10;
      }
    }
    else {
      pvVar4 = (void *)*param_1;
    }
    pvVar8 = (void *)((int)pvVar4 + iVar9 * 0x10);
    param_1[2] = iVar2;
  }
  if (pvVar8 != (void *)0x0) {
    iVar6 = param_2[1];
    iVar2 = param_2[2];
    iVar5 = param_2[3];
    *(int *)((int)pvVar4 + iVar9 * 0x10) = *param_2;
    *(int *)((int)pvVar8 + 4) = iVar6;
    *(int *)((int)pvVar8 + 8) = iVar2;
    *(int *)((int)pvVar8 + 0xc) = iVar5;
  }
  return;
}

