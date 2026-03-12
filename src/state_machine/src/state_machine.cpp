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


// This is where the real statemachine should go. Currently it is the same as the example.
// --- FORWARD STATE ---
class ForwardState : public yasmin::State
{
public:
  ForwardState()
  : yasmin::State({"time_up", "running"}) {}

  std::string execute(yasmin::Blackboard::SharedPtr blackboard) override
  {
    (void)blackboard;
    if (!started_) {
      start_time_ = std::chrono::steady_clock::now();
      started_ = true;
      std::cout << "[ForwardState] Started" << std::endl;
    }

    auto now = std::chrono::steady_clock::now();
    auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(now - start_time_).count();

    if (elapsed >= 3) {
      started_ = false;
      return "time_up";
    }
    return "running";
  }

private:
  std::chrono::steady_clock::time_point start_time_;
  bool started_ = false;
};

// --- ROTATE STATE ---
class RotateState : public yasmin::State
{
public:
  RotateState()
  : yasmin::State({"time_up", "running"}) {}                 //constructor - returns outcome "time up"

  std::string execute(yasmin::Blackboard::SharedPtr blackboard) override
  {
    (void)blackboard;
    if (!started_) {
      start_time_ = std::chrono::steady_clock::now();
      started_ = true;
      std::cout << "[RotateState] Started" << std::endl;
    }

    auto now = std::chrono::steady_clock::now();
    auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(now - start_time_).count();

    if (elapsed >= 2) {
      started_ = false;
      return "time_up";
    }
    return "running";
  }

private:
  std::chrono::steady_clock::time_point start_time_;
  bool started_ = false;
};

class state_machine_node : public rclcpp::Node
{
public:
  state_machine_node()
  : Node("state_machine_node")
  {

    state_machine_ = std::make_shared<yasmin::StateMachine>(std::set<std::string>{"final_outcome"});

    // Use unordered_map to match yasmin::Transitions
    std::unordered_map<std::string, std::string> forward_transitions = {{"time_up", "ROTATE"},
      {"running", "FORWARD"}};
    std::unordered_map<std::string, std::string> rotate_transitions = {{"time_up", "FORWARD"},
      {"running", "ROTATE"}};

    // Add states with their transition maps
    state_machine_->add_state("FORWARD", std::make_shared<ForwardState>(), forward_transitions);
    state_machine_->add_state("ROTATE", std::make_shared<RotateState>(), rotate_transitions);


    state_machine_->set_start_state("FORWARD");

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
