#include <memory>
#include <string>
#include <unordered_map>
#include <set>
#include <chrono>
#include <iostream>

#include "rclcpp/rclcpp.hpp"
#include "yasmin/state_machine.hpp"
#include "yasmin/state.hpp"
#include "yasmin/blackboard.hpp"
#include "yasmin_viewer/yasmin_viewer_pub.hpp"

#include <messages/msg/pid_input.hpp>
class StartingState : public yasmin::State
{
public:
  // you put the transition codes, or exit codes, here (can put as many as want, but need to be able to return it)
  StartingState()
  : State({"finished"}) {}

  std::string execute() override
  {
    messages::msg::PIDInput msg;

    // goes down for 0.2 seconds at 0.2 power
    msg.x_mode = false;
    msg.z_mode = false;
    msg.roll_mode = false;
    msg.pitch_mode = false;
    msg.yaw_mode = false;

    msg.y_power = -0.2f;

    std::this_thread::sleep_for(0.2);

    return "finished";
  }
};

class state_machine_node : public rclcpp::Node
{
public:
  state_machine_node()
  : Node("state_machine_node")
  {

    // the string here is the code you throw when you want it to shut down
    // throwing a transition that doesnt exist also shuts it down
    state_machine_ = std::make_shared<yasmin::StateMachine>(std::set<std::string>{"complete"});

    // adds a state (the name of it that we make up, not tied to anythig), the actual state, and then the transitions that it can take
    state_machine_->add_state("START", std::make_shared<StartingState>(), {{"finished", "IDK"}});

    state_machine_->set_start_state("START");

    yasmin_pub_ = std::make_unique<yasmin_viewer::YasminViewerPub>(state_machine_, "TigerFish_SM");

    timer_ = this->create_wall_timer(
      std::chrono::milliseconds(100),
      [this]() {(*state_machine_)();});

    RCLCPP_INFO(this->get_logger(), "State machine initialized successfully!");
  }

private:
  std::shared_ptr<yasmin::StateMachine> state_machine_;
  rclcpp::TimerBase::SharedPtr timer_;
  std::unique_ptr<yasmin_viewer::YasminViewerPub> yasmin_pub_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<state_machine_node>());
  rclcpp::shutdown();
  return 0;
}
