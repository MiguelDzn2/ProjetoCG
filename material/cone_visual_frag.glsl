in vec4 fragmentColor; // Received from vertex shader (contains gradient in .a)
in vec3 fragmentNormal; // Received from vertex shader

uniform vec3 baseColor;      // Base color of the cone (e.g., yellow for visibility)
uniform float opacity;       // Overall opacity multiplier

out vec4 FragColor;

void main()
{
    // Use the alpha from fragmentColor (which is interpolated vertexColor.a) for transparency
    // The RGB components of fragmentColor are currently 1,1,1 from the geometry, 
    // we will use baseColor for the actual cone color.
    FragColor = vec4(baseColor, fragmentColor.a * opacity);
} 