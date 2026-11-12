/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0078a6ac(int *param_1,undefined4 param_2)

{
  bool bVar1;
  uint uVar2;
  int iVar3;
  int iVar4;
  int *piVar5;
  int iVar6;
  int iVar7;
  int iVar8;
  int iVar9;
  int iVar10;
  int local_58;
  int local_54;
  int local_50;
  int local_4c;
  undefined4 local_48;
  undefined4 local_44;
  undefined4 local_40;
  undefined4 local_3c;
  undefined4 local_38;
  undefined4 local_34;
  uint local_30;
  uint local_2c;
  
  FUN_006cfa50(&local_58);
  uVar2 = (uint)(*(byte *)((int)param_1 + 0x69) >> 7);
  if (uVar2 == 0) {
    FUN_006cfa70(param_2);
    local_30 = uVar2;
    local_2c = uVar2;
    iVar4 = FUN_0075eba0(param_1,param_2,&local_58,&local_30);
    if ((iVar4 != 0) || (iVar4 = FUN_006cfa38(param_2), iVar4 == 0)) {
      (**(code **)(*param_1 + 0x60))(param_1,param_2);
    }
    FUN_006cfaa8(param_2);
  }
  else {
    (**(code **)(*param_1 + 0x60))(param_1,param_2);
  }
  iVar4 = param_1[0xc];
  if (0 < iVar4) {
    iVar7 = 0;
    iVar6 = 1;
    do {
      while (iVar9 = *(int *)(param_1[10] + iVar7), (*(byte *)(iVar9 + 0x68) & 2) != 0) {
        if (*(int *)(iVar9 + 0x24) == 0) {
          if (((((local_58 + local_50 <= *(int *)(iVar9 + 0x10)) ||
                (local_54 + local_4c <= *(int *)(iVar9 + 0x14))) ||
               ((*(int *)(iVar9 + 0x10) + *(int *)(iVar9 + 0x18) <= local_58 ||
                ((*(int *)(iVar9 + 0x14) + *(int *)(iVar9 + 0x1c) <= local_54 || (local_50 < 1))))))
              || (local_4c < 1)) || ((*(int *)(iVar9 + 0x18) < 1 || (*(int *)(iVar9 + 0x1c) < 1))))
          break;
          FUN_006cfa70(param_2);
          if (*(char *)(iVar9 + 0x69) < '\0') {
            local_40 = *(undefined4 *)(iVar9 + 0x10);
            local_3c = *(undefined4 *)(iVar9 + 0x14);
            FUN_006cfb04(param_2,&local_40);
            piVar5 = *(int **)(iVar9 + 0x40);
            if (piVar5 == (int *)0x0) {
              FUN_00789950(iVar9,param_2);
            }
            else {
              (**(code **)(*piVar5 + 8))(piVar5,param_2);
            }
          }
          else {
            iVar4 = FUN_006cf7f8(param_2,iVar9 + 0x10);
            if (iVar4 != 0) {
              iVar4 = param_1[0xc];
              if (iVar6 < iVar4) {
                iVar10 = iVar6 << 2;
                bVar1 = true;
                iVar8 = iVar6;
                do {
                  iVar8 = iVar8 + 1;
                  iVar3 = *(int *)(param_1[10] + iVar10);
                  iVar10 = iVar10 + 4;
                  if ((((*(byte *)(iVar3 + 0x68) & 4) != 0) && ((*(byte *)(iVar3 + 0x68) & 2) != 0))
                     && (*(int *)(iVar3 + 0x24) == 0)) {
                    FUN_006cf9e8(param_2,iVar3 + 0x10);
                    iVar4 = param_1[0xc];
                    bVar1 = false;
                  }
                } while (iVar8 < iVar4);
                if ((!bVar1) && (iVar4 = FUN_006cfa38(param_2), iVar4 != 0)) goto LAB_0078a8c4;
              }
              local_38 = *(undefined4 *)(iVar9 + 0x10);
              local_34 = *(undefined4 *)(iVar9 + 0x14);
              FUN_006cfb04(param_2,&local_38);
              piVar5 = *(int **)(iVar9 + 0x40);
              if (piVar5 == (int *)0x0) {
                FUN_00789950(iVar9,param_2);
              }
              else {
                (**(code **)(*piVar5 + 8))(piVar5,param_2);
              }
            }
          }
LAB_0078a8c4:
          FUN_006cfaa8(param_2);
          iVar4 = param_1[0xc];
        }
        else {
          FUN_006cfa70(param_2);
          FUN_006cfbc4(param_2,*(undefined4 *)(iVar9 + 0x24));
          if (((*(char *)(iVar9 + 0x69) < '\0') && (iVar4 = FUN_006cfa38(param_2), iVar4 == 0)) ||
             (iVar4 = FUN_006cf7f8(param_2,iVar9 + 0x10), iVar4 != 0)) {
            local_48 = *(undefined4 *)(iVar9 + 0x10);
            local_44 = *(undefined4 *)(iVar9 + 0x14);
            FUN_006cfb04(param_2,&local_48);
            piVar5 = *(int **)(iVar9 + 0x40);
            if (piVar5 == (int *)0x0) {
              FUN_00789950(iVar9,param_2);
            }
            else {
              (**(code **)(*piVar5 + 8))(piVar5,param_2);
            }
          }
          FUN_006cfaa8(param_2);
          iVar4 = param_1[0xc];
        }
        iVar7 = iVar7 + 4;
        bVar1 = iVar4 <= iVar6;
        iVar6 = iVar6 + 1;
        if (bVar1) goto LAB_0078a7bc;
      }
      iVar7 = iVar7 + 4;
      bVar1 = iVar6 < iVar4;
      iVar6 = iVar6 + 1;
    } while (bVar1);
  }
LAB_0078a7bc:
  FUN_006cfa70(param_2);
  (**(code **)(*param_1 + 100))(param_1,param_2);
  FUN_006cfaa8(param_2);
  return;
}

