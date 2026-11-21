#pragma once

#include <cmath>
#include <algorithm>

namespace diff_drive {

// 逆解参数
struct IKParams {
    float wheel_radius   = 0.035f;    // r [m]  3.5cm
    float track_width    = 0.5f;    // b [m]    50cm
    float max_wheel_rads = 300.0f;  // 单轮最大角速度 [rad/s]  **未定
};

// 逆解输出
struct IKOutput {
    float phi_dot_L = 0.0f;   // 左轮目标角速度 [rad/s]
    float phi_dot_R = 0.0f;   // 右轮目标角速度 [rad/s]
    float v_x_used  = 0.0f;   // 限幅后实际 v_x [m/s]
    float omega_used = 0.0f;  // 限幅后实际 omega [rad/s]
    bool  saturated  = false; // 是否发生归一化限幅
};

// 一阶低通平滑器（作用于 v_x, omega，在逆解之前调用）
class CommandSmoother {
public:
    CommandSmoother(float tau, float dt) {
        if (tau > 0.0f && dt > 0.0f) {
            alpha_ = dt / (tau + dt);               //tau越大滤波越重
        } else {
            alpha_ = 1.0f;
        }
    }

    void reset() { inited_ = false; }

    void smooth(float vx_in, float om_in, float& vx_out, float& om_out) {
        if (!inited_) {
            vx_filt_ = vx_in;
            om_filt_ = om_in;
            inited_  = true;
        } else {
            vx_filt_ += alpha_ * (vx_in - vx_filt_);
            om_filt_ += alpha_ * (om_in - om_filt_);
        }
        vx_out = vx_filt_;
        om_out = om_filt_;
    }

private:
    float alpha_;
    float vx_filt_ = 0.0f;
    float om_filt_ = 0.0f;
    bool  inited_  = false;
};

// 差速逆运动学求解器
class DiffDriveIK {
public:
    explicit DiffDriveIK(const IKParams& p = IKParams{}) : p_(p) {}

    void setParams(const IKParams& p) { p_ = p; }
    const IKParams& params() const { return p_; }

    // 核心逆解：带归一化限幅，保持曲率不变
    IKOutput solve(float v_x, float omega) const {
        IKOutput out;
        const float r = p_.wheel_radius;
        const float b = p_.track_width;

        // 1) 左右轮心纵向速度 [m/s]
        float v_L = v_x - omega * b * 0.5f;
        float v_R = v_x + omega * b * 0.5f;

        // 2) 归一化限幅：按 max(|v_L|,|v_R|) 等比缩放，保持曲率
        const float max_v = p_.max_wheel_rads * r;
        const float vmax  = std::max(std::fabs(v_L), std::fabs(v_R));

        if (vmax > max_v && vmax > 1e-6f) {
            const float k = max_v / vmax;
            v_L *= k;
            v_R *= k;
            out.saturated  = true;
            out.v_x_used   = 0.5f * (v_L + v_R);
            out.omega_used = (v_R - v_L) / b;
        } else {
            out.v_x_used   = v_x;
            out.omega_used = omega;
        }

        // 3) 线速度 -> 角速度 [rad/s]
        out.phi_dot_L = v_L / r;
        out.phi_dot_R = v_R / r;
        return out;
    }

    // 正解校验：由轮速反推车体运动
    static void forward(const IKParams& p, float phi_dot_L, float phi_dot_R,
                        float& v_x, float& omega) {
        v_x   = 0.5f * p.wheel_radius * (phi_dot_L + phi_dot_R);
        omega = p.wheel_radius * (phi_dot_R - phi_dot_L) / p.track_width;
    }

private:
    IKParams p_;
};

} // namespace diff_drive