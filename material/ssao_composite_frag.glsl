#version 330 core

in vec2 v_texCoords; // Renamed from texCoords to match ssao_blur_vert.glsl output

out vec4 FragColor;

uniform sampler2D sceneTexture;      // The normally rendered scene
uniform sampler2D ssaoBlurTexture;   // The blurred SSAO map

void main() {
    vec3 originalSceneColor = texture(sceneTexture, v_texCoords).rgb;
    float occlusion = texture(ssaoBlurTexture, v_texCoords).r;

    // Revert to original multiplication:
    vec3 finalColor = originalSceneColor * occlusion;

    // Original multiplication:
    // vec3 finalColor = originalSceneColor * occlusion;

    FragColor = vec4(finalColor, 1.0);
} 