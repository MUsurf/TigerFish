## Gate States Overview

The gate portion of the state machine consists of two parts:
 
 1. Align_gate:
        Alignment state: for locating the gate and aligning ourselves with the side distinguished by our role. 
 2. Thru_gate:
        The state that actually takes the sub through the gate. It has an option to proceed "with style" (perform a 360 degree spin on the yaw axis). This option is enabled/disabled upon state initialization based information from the Blackboard.

The states follow mostly the above order; however, in the event that the sub somehow becomes horribly lost, it may return to the alignment state to reorient itself.