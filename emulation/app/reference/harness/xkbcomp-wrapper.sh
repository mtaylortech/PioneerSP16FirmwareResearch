#!/bin/sh
export DYLD_LIBRARY_PATH='<RESEARCH_ROOT>/experiments/post-parent-startup-20261008-150354/xquartz-package/XQuartzComponent.pkg/Payload/opt/X11/lib'
exec '<RESEARCH_ROOT>/experiments/post-parent-startup-20261008-150354/display-bin/xkbcomp' "$@"
