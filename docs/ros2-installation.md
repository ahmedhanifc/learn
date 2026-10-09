# Install ROS 2 Lyrical on Ubuntu 26.04

This guide is tailored to your Ubuntu 26.04 (Resolute) laptop and Bash terminal. It installs ROS 2 Lyrical with desktop tools and verifies that two ROS programs can communicate. Commands below are for you to run; writing this guide does not install anything.

Run each code block in order. Wait for it to finish before continuing. If a command fails, stop and share its output. When `sudo` asks for your password, type your Ubuntu login password and press Enter; no characters appear while typing.

## 1. Check your system and leave the Python environment

```bash
cat /etc/os-release
dpkg --print-architecture
```

Expect Ubuntu `26.04`, codename `resolute`, and architecture `amd64` on this laptop. These instructions also support `arm64`. Stop if the Ubuntu version differs.

Your earlier prompt showed `(ds)`. If that is a Conda environment, run:

```bash
conda deactivate
```

Repeat if another Conda environment such as `(base)` remains active. If it is a Python virtual environment instead, use `deactivate`. Skip this when no environment is active. Use the system Python for this installation.

## 2. Disable the repository from the old ROS instructions

The earlier setup left `/etc/apt/sources.list.d/ros-latest.list` pointing to the ROS 1 repository. Preserve it as a disabled backup:

```bash
if [ -f /etc/apt/sources.list.d/ros-latest.list ]; then
  sudo mv --backup=numbered /etc/apt/sources.list.d/ros-latest.list \
    /etc/apt/sources.list.d/ros-latest.list.disabled
fi
```

The block does nothing if you already disabled the file. Do not repeat the old `apt-key` command.

## 3. Prepare APT and check the locale

```bash
sudo apt update
```

Continue only if the update succeeds.

```bash
sudo apt install curl python3 locales software-properties-common
```

```bash
locale charmap
```

Your machine already reported `UTF-8`. If it still does, skip the next block. Otherwise run:

```bash
sudo locale-gen en_US.UTF-8
sudo update-locale LANG=en_US.UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
locale charmap
```

Check that the final output is `UTF-8`.

## 4. Enable Ubuntu Universe

Universe was already enabled when your machine was inspected. Running this again is safe:

```bash
sudo add-apt-repository universe
```

Press Enter if prompted to continue.

## 5. Install the ROS repository configuration

Keep these commands in the same terminal so the version variable remains available.

First retrieve the latest repository-configuration package version:

```bash
ROS_APT_SOURCE_VERSION=$(curl -fsSL \
  https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest \
  | /usr/bin/python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"])')
printf 'Repository package version: %s\n' "$ROS_APT_SOURCE_VERSION"
```

You should see a nonempty version number and no errors. If the request fails or the version is empty, stop here.

Download the package specifically for Ubuntu Resolute:

```bash
curl -fL -o /tmp/ros2-apt-source.deb \
  "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.resolute_all.deb"
```

After the download succeeds, install it:

```bash
sudo dpkg -i /tmp/ros2-apt-source.deb
```

This sets up the ROS 2 package source and signing key.

## 6. Refresh packages and update Ubuntu

```bash
sudo apt update
```

```bash
sudo apt upgrade
```

The upgrade updates existing Ubuntu packages too. Read the proposed changes, then enter `Y` to proceed. If Ubuntu requests a restart, save your work and restart before continuing. Open a new terminal afterward and leave any active Conda environment again.

## 7. Install ROS 2 and development tools

Check that APT can find Lyrical:

```bash
apt-cache policy ros-lyrical-desktop
```

The `Candidate` field should show a version. If it says `(none)` or there is no output, stop and check the repository setup and the preceding `apt update` output.

Preview the installation:

```bash
apt-get --simulate install ros-lyrical-desktop ros-dev-tools
```

If the preview reports unmet dependencies or unexpected removals, share that output before proceeding. Otherwise install:

```bash
sudo apt install ros-lyrical-desktop ros-dev-tools
```

Review the disk-space requirement and package list, then enter `Y`. Wait until the terminal prompt returns successfully.

## 8. Activate ROS in this terminal

```bash
source /opt/ros/lyrical/setup.bash
echo "$ROS_DISTRO"
ros2 --help
```

Expect `lyrical` followed by ROS command-line help. Run the `source` command in each new terminal where you want to use ROS.

## 9. Verify communication between two programs

Open two terminals. Leave any active Conda or virtual environment in each one, as in step 1.

In **terminal 1**, run:

```bash
source /opt/ros/lyrical/setup.bash
ros2 run demo_nodes_cpp talker
```

Leave it running. You should see numbered messages being published.

In **terminal 2**, run:

```bash
source /opt/ros/lyrical/setup.bash
ros2 run demo_nodes_py listener
```

You should see matching messages arriving. That is the main installation success check. Press **Ctrl+C** in both terminals when finished.

## 10. Check the desktop visualizer

In a terminal on your Ubuntu desktop:

```bash
source /opt/ros/lyrical/setup.bash
rviz2
```

An RViz window should open. An empty scene is expected before you configure any robot data. Close the window when finished.

## 11. Optional: load ROS automatically in new Bash terminals

If you prefer to activate ROS manually, skip this step. Otherwise add its setup command once:

```bash
if ! grep -qxF 'source /opt/ros/lyrical/setup.bash' "$HOME/.bashrc"; then
  printf '\nsource /opt/ros/lyrical/setup.bash\n' >> "$HOME/.bashrc"
fi
```

Open a new terminal and check:

```bash
echo "$ROS_DISTRO"
ros2 --help
```

Continue to leave Conda environments before running ROS commands, even if ROS loads automatically.

## If something goes wrong

| Symptom | Next action |
| --- | --- |
| `apt-key: command not found` | Use step 5; this guide does not need `apt-key`. |
| APT errors mention `packages.ros.org/ros/ubuntu` and `resolute` | Confirm the old ROS 1 source was disabled in step 2. |
| `Unable to locate package ros-lyrical-desktop` | Check steps 5–7 and share the complete `sudo apt update` output. |
| `ros2: command not found` | Run `source /opt/ros/lyrical/setup.bash` in that terminal. |
| The setup file does not exist | The installation in step 7 has not completed successfully. |
| Python import errors | Leave Conda/virtual environments, open a clean terminal, and source ROS again. |
| The listener receives nothing | Keep both terminals on the same machine and share the output from both programs. |

For troubleshooting, collect:

```bash
cat /etc/os-release
command -v python3
echo "$ROS_DISTRO"
apt-cache policy ros-lyrical-desktop
```

## References

- [Official Ubuntu installation procedure supplied in your request](https://github.com/ros2/ros2_documentation/blob/rolling/source/Get-Started/Installation/Ubuntu-Install-Debs.rst).
- [Official Lyrical platform support](https://github.com/ros2/ros2_documentation/blob/rolling/source/Releases/lyrical/supported-platforms.rst): Ubuntu 26.04 on amd64 and arm64 supports binary packages.
- [ROS repository configuration package](https://github.com/ros-infrastructure/ros-apt-source).

The supplied documentation lives on the `rolling` branch and uses distribution placeholders. This guide fills those in with `lyrical` for your Ubuntu 26.04 installation.
