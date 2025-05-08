// Inputs from vertex shader
in vec3 vs_out_positionView;
in vec3 vs_out_normalView;

// Output G-Buffer textures
layout (location = 0) out vec3 gPositionView; // View-space position
layout (location = 1) out vec3 gNormalView;   // View-space normal

void main()
{
    gPositionView = vs_out_positionView;
    gNormalView = normalize(vs_out_normalView); // Ensure normal is unit length after interpolation
} 