# ROS 2 learning guide

For your Ubuntu 26.04 laptop with ROS 2 Lyrical. Prepared 8 October 2026.

You have installed ROS, activated its environment, and tried the talker/listener demo. Start with session 1 below; you do not need to reinstall anything. Your [installation guide](ros2-installation.md) remains available for setup questions.

The goal is to understand an unfamiliar ROS system, inspect its communication, and build a small Python application yourself. The exercises intentionally have no solutions: predict what will happen, run an experiment, and explain the result in your own words.

## Start here

Use the official [First steps with ROS learning path](https://github.com/ros2/ros2_documentation/blob/rolling/source/First-Steps.rst) as your main reading list. It connects the concepts to runnable demonstrations. Read its introduction today, then do session 1 rather than reading everything at once.

Plan for roughly 8–10 sessions of 45–90 minutes, at your own pace. These are suggested study blocks, not a deadline. Spend more time on any checkpoint you cannot explain without looking at the tutorial.

## A small resource library

| Resource | Why use it? | When |
| --- | --- | --- |
| [Official first-steps path](https://github.com/ros2/ros2_documentation/blob/rolling/source/First-Steps.rst) | Your main sequence for concepts, communication, debugging, launch, and recording. | Sessions 1–6 |
| [Official Turtlesim walkthrough](https://github.com/ros2/ros2_documentation/blob/rolling/source/Get-Started/Introducing-Turtlesim/Introducing-Turtlesim.rst) | A visual, interactive environment for experimenting without robot hardware. | Sessions 2–4 |
| [Official workspace and client-library tutorials](https://github.com/ros2/ros2_documentation/tree/rolling/source/ROS-Framework/client-libraries/Working-with-Client-Libraries) | Worked examples for building packages and writing Python nodes. Use only the selected lessons below initially. | Sessions 7–8 |
| [About ROS client libraries](https://github.com/ros2/ros2_documentation/blob/rolling/source/ROS-Framework/About-Client-Libraries.rst) | Context for the Python and C++ APIs you encounter in examples. | Before session 8 |
| [Python tutorial](https://docs.python.org/3/tutorial/) | Optional refresher on functions, modules, and classes. Assumes some programming experience. | Only if Python syntax gets in your way |

The ROS links use the official documentation source on GitHub because the documentation website blocked automated access during research. GitHub renders the prose and code, although some `:doc:` references remain plain text. The first-steps page gives the relative paths to the individual lessons; open those under the repository's `source` directory.

These links point to the evolving `rolling` documentation branch. Your installed release is **Lyrical**. Substitute `lyrical` for `{DISTRO}` in generic setup examples, and keep `/opt/ros/lyrical/setup.bash`. If a tutorial explicitly requires a Rolling-only feature, defer it; do not change ROS releases to complete this beginner guide.

## Before each session

Open a terminal and leave any active Conda or Python virtual environment. Then run:

```bash
source /opt/ros/lyrical/setup.bash
echo "$ROS_DISTRO"
```

Expect `lyrical`. Repeat the setup in each terminal used for ROS. Once you build your own workspace, its tutorial will also explain how to source the workspace overlay.

Keep a short notebook with four entries per experiment:

1. What I predict.
2. What I ran or changed.
3. What I observed.
4. What I still cannot explain.

## Session 1 — Investigate the demo you already ran

**Read:** The fundamental-concepts section of the first-steps path, especially its node and communication-interface references.

**Practice:** Run the talker and listener in separate terminals. In a third, use these inspection tools:

```bash
ros2 node list
ros2 topic list
ros2 topic info /chatter
ros2 topic echo /chatter
```

Stop `echo` with Ctrl+C. Inspect a node using the name returned by `ros2 node list` and `ros2 node info`. Use `ros2 node info --help` if you need the syntax.

**Experiments:** Stop only the listener, then restart it. Start a second listener. Predict each result before trying it.

**Checkpoint:** Draw the demo's communication diagram with names and arrows. Explain what each node does, what travels over the topic, and which observations support your explanation.

## Session 2 — Make the concepts visible with Turtlesim

**Read and follow:** The Turtlesim walkthrough in the resource library. It provides the setup commands and practical demonstrations.

First check whether it is already available:

```bash
ros2 pkg executables turtlesim
```

If it is missing after sourcing ROS, follow the tutorial's installation step using `ros-lyrical-turtlesim`.

**Practice:** Start the simulator and keyboard controller in separate terminals. Keep keyboard focus in the controller terminal when pressing the arrow keys. Discover the active nodes and topics, and inspect the message type used for movement.

**Experiment:** Compare the topics before and after starting the keyboard controller. Record which changes you see and which you expected but did not see.

**Checkpoint:** Identify the source and recipient of movement commands using inspection output rather than guessing from program names.

## Session 3 — Services and parameters

**Read:** The services and parameters tutorials linked from the main learning path. Continue using Turtlesim so you can see the effects immediately.

**Practice:** Follow the worked examples for discovering services, examining their request types, calling a service, and reading or changing a parameter.

**Independent challenges:** Create another turtle, change a visual setting, and restore that setting. Find the appropriate interfaces using the inspection tools and documentation rather than copying an entire command sequence.

**Checkpoint:** Explain when you would choose a topic, a service, or a parameter for an application. Support each choice with one experiment you performed.

## Session 4 — Actions

**Read:** The actions tutorial linked from the first-steps path.

**Practice:** Complete its Turtlesim action example. Inspect the action interface and observe its goal, feedback, and result. Try cancellation as described in the tutorial.

**Independent challenge:** Choose a task that takes several seconds. Sketch what information you would want at its start, during execution, and at completion. Decide whether an action fits and justify your choice.

**Checkpoint:** Explain how the interaction differs from the service experiment in session 3, including what happens when the caller wants to stop the task.

## Session 5 — Observe and launch a system

**Read:** The `rqt_console` and launch tutorials linked from the main learning path.

**Practice:** Inspect logs, then follow the launch example to start multiple nodes together. Examine which settings belong to each node.

**Independent challenge:** Deliberately use an incorrect node or topic name in a command, then use the inspection tools to identify the mistake. Keep a record of the symptom and how you found its cause.

**Checkpoint:** Restart the tutorial system from a fresh terminal and explain how its processes were started and configured.

## Session 6 — Record and replay

**Read:** The recording and playback tutorial linked from the first-steps path.

**Practice:** Record a short, deliberate sequence of turtle movements. Inspect the recording, stop the original controller, and replay the data with a suitable simulator running.

**Independent challenge:** Predict how the replay could differ if the turtle starts from another position. Test your prediction and document the result.

**Checkpoint:** Explain what your recording contains and what other parts of the system you still needed during playback.

## Session 7 — Create your development workspace

**Read and follow, in order:** These selected lessons from the client-library tutorial collection:

1. [Creating a workspace](https://github.com/ros2/ros2_documentation/tree/rolling/source/ROS-Framework/client-libraries/Working-with-Client-Libraries/Creating-A-Workspace).
2. [Creating your first package](https://github.com/ros2/ros2_documentation/blob/rolling/source/ROS-Framework/client-libraries/Working-with-Client-Libraries/Creating-Your-First-ROS2-Package.rst) — choose the Python instructions.

**Practice:** Build a small workspace with `colcon` using the tutorial. Run its package from a fresh terminal after sourcing the required environments.

**Checkpoint:** Identify your source files, build outputs, and installed package files. Explain why a successful build alone may not make a command available in another terminal.

## Session 8 — Write Python nodes

**Read:** The client-library overview, then [Writing a simple Python publisher and subscriber](https://github.com/ros2/ros2_documentation/blob/rolling/source/ROS-Framework/client-libraries/Working-with-Client-Libraries/Writing-A-Simple-Py-Publisher-And-Subscriber.rst).

**Practice:** Work through the example. Locate the timer, callback, message type, and entry point in the code. Inspect your running nodes with the tools from session 1.

**Independent challenges:** Change the published content and rate. Run another subscriber. Deliberately mismatch a topic name, diagnose the symptom, and repair it.

**Checkpoint:** Build a similar pair of nodes from your own notes. Explain why each important part of the code is necessary before consulting the example again.

If classes or imports are unfamiliar, use the Python tutorial's sections on functions, modules, and classes before continuing.

## Sessions 9–10 — A small independent project

Build a **Turtlesim movement experiment**. Choose a simple motion pattern yourself; a perfect geometric shape is unnecessary.

Acceptance criteria:

- A Python node sends movement commands.
- A second Python node observes the turtle's reported position and prints useful information.
- A launch file starts the components needed for the experiment.
- You can inspect the running nodes and message types.
- You can record a short run and explain the playback setup.
- A short README tells you how to repeat the experiment from a fresh terminal.

First draw the proposed node/topic diagram. Implement one working interaction at a time. Use the tutorials as references, but write your own project code. Parameterizing a setting is an optional extension after the basic project works.

## What to study afterward

Choose a direction after completing the project:

| Interest | Next subjects to investigate |
| --- | --- |
| Mobile robots | Coordinate frames, `tf2`, robot descriptions, simulation, then navigation |
| Robot arms | Coordinate frames, joints, robot descriptions, then motion planning |
| Sensors and perception | Sensor message types, timestamps, visualization, then processing pipelines |
| Reliable ROS applications | QoS, executors and callbacks, testing, lifecycle nodes |

Treat these as later study topics. Pick resources for your chosen direction when you reach it, so this guide stays focused on your immediate foundations.

## Progress tracker

- [x] Install ROS 2 and activate Lyrical.
- [ ] Explain and inspect the talker/listener demo.
- [ ] Explore Turtlesim nodes and topics.
- [ ] Use services and parameters.
- [ ] Complete an action experiment.
- [ ] Inspect logs and use a launch file.
- [ ] Record and replay messages.
- [ ] Create and build a Python package.
- [ ] Write and debug your own publisher/subscriber pair.
- [ ] Complete the independent project and its README.

Your next action: open the first-steps resource, then complete session 1 with your existing demo.
