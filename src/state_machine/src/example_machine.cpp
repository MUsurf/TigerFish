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


class ExampleState : public yasmin::State
{
public:
  // you put the transition codes, or exit codes, here (can put as many as want, but need to be able to return it)
  ExampleState()
  : State({"ExitCode1", "ExitCode2"}) {}

  std::string execute() override
  {
    // DO THINGS HERE

    if (1) {
      return "ExitCode1";
    } else {
      return "ExitCode2";
    }
  }
};

class state_machine_node : public rclcpp::Node
{
public:
  state_machine_node()
  : Node("state_machine_node")
  {

    // the string here is the code you throw when you want it to shut down
    // throwing a transition that doesnt exist also shuts it down (might throw an error, so prob dont do that)
    state_machine_ = std::make_shared<yasmin::StateMachine>(std::set<std::string>{"complete"});

    // adds a state (the name of it that we make up, not tied to anythig), the actual state, and then the transitions that it can take
    // for the transitions, it is pairs of what it returns, then what to goes to, so for instance if it returns "ExitCode1", it goes back into the state ("EXAMPLE")
    // and if it returns "ExitCode2", it exits the state machine (which if it is the only one ends the program)
    state_machine_->add_state(
      "EXAMPLE",
      std::make_shared<ExampleState>(), {{"ExitCode1", "EXAMPLE"}, {"ExitCode2", "complete"}});

    state_machine_->set_start_state("EXAMPLE");

    // the rest idk man, you got this though

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
