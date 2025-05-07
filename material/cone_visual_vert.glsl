in vec3 vertexPosition;
in vec4 vertexColor; // RGBA, we'll use A for transparency gradient
in vec3 vertexNormal; // Included for completeness, might not be used by this specific shader
in vec2 vertexUV;     // Included for completeness

out vec4 fragmentColor; // Pass color (including gradient alpha) to fragment shader
out vec3 fragmentNormal;

uniform mat4 modelMatrix;
uniform mat4 viewMatrix;
uniform mat4 projectionMatrix;

void main()
{
    gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(vertexPosition, 1.0);
    fragmentColor = vertexColor; // Pass the color (with gradient alpha) through
    fragmentNormal = normalize(mat3(modelMatrix) * vertexNormal); // Transform normal to world space
} 