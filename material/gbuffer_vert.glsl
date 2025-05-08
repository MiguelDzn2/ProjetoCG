// Vertex attributes
layout (location = 0) in vec3 vertexPosition; // Corresponds to a_position
layout (location = 1) in vec2 vertexUV;       // Corresponds to a_texCoord (unused here but often present)
layout (location = 2) in vec3 vertexNormal;   // Corresponds to a_normal

// Uniforms
uniform mat4 modelMatrix;
uniform mat4 viewMatrix;
uniform mat4 projectionMatrix;

// Outputs to fragment shader
out vec3 vs_out_positionView; // Vertex position in view space
out vec3 vs_out_normalView;   // Vertex normal in view space

void main()
{
    // Transform vertex position to world space, then to view space
    vec4 positionWorld = modelMatrix * vec4(vertexPosition, 1.0);
    vs_out_positionView = vec3(viewMatrix * positionWorld);

    // Transform vertex normal to view space
    // Normal matrix is the transpose of the inverse of the model-view matrix (upper 3x3)
    mat3 normalMatrix = mat3(transpose(inverse(viewMatrix * modelMatrix)));
    vs_out_normalView = normalize(normalMatrix * vertexNormal);

    // Transform vertex position to clip space for rasterization
    gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(vertexPosition, 1.0);
} 