/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_002bfe6c(int *param_1,int param_2)

{
  if (param_2 == 0) {
    param_1 = param_1 + 0xb;
    FUN_0069769c(param_1);
    FUN_0069769c(param_1,1);
    FUN_0069769c(param_1,2);
    FUN_0069769c(param_1,3);
    FUN_0069769c(param_1,4);
    FUN_0069769c(param_1,5);
    FUN_0069769c(param_1,6);
    return;
  }
  (**(code **)(*param_1 + 0x38))(param_1,0);
  FUN_0069c37c(param_1 + 0xb,0,0x32);
  return;
}

