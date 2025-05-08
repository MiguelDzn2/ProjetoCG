out vec4 FragColor;

in VS_OUT {
    vec2 texCoords;
} fs_in;

uniform sampler2D gPositionView;
uniform sampler2D gNormalView;
uniform sampler2D texNoise;

uniform vec3 samples[64]; // KERNEL_SIZE will be a const in shader or passed if dynamic
uniform mat4 projectionMatrix;

uniform float radius = 0.5;
uniform float bias = 0.025;
uniform int kernelSize = 64;
uniform float ssaoPower = 1.0;

// Tile noise texture over screen
uniform vec2 noiseScale; // e.g., vec2(screenWidth/noiseSize, screenHeight/noiseSize)

void main()
{
    // Get G-Buffer values
    vec3 fragPosView = texture(gPositionView, fs_in.texCoords).xyz;
    vec3 normalView = normalize(texture(gNormalView, fs_in.texCoords).rgb);
    vec3 randomVec = normalize(texture(texNoise, fs_in.texCoords * noiseScale).xyz); // Should be normalized if not already

    // Create TBN matrix (Tangent, Bitangent, Normal)
    // to orient the sampling kernel with the surface normal
    vec3 tangent = normalize(randomVec - normalView * dot(randomVec, normalView));
    vec3 bitangent = cross(normalView, tangent);
    mat3 TBN = mat3(tangent, bitangent, normalView);

    float occlusion = 0.0;
    for(int i = 0; i < kernelSize; ++i)
    {
        // Get sample position from kernel (defined in tangent space)
        // Transform sample to view space and offset by current fragment's view position
        vec3 samplePosKernel = samples[i]; // Already in hemisphere, scaled
        vec3 samplePosView = TBN * samplePosKernel; // Transform to view-space orientation
        samplePosView = fragPosView + samplePosView * radius; // Position relative to current fragment and scale by radius

        // Project sample position to screen space [0, 1]
        vec4 offset = projectionMatrix * vec4(samplePosView, 1.0);
        offset.xyz /= offset.w; // Perspective divide
        offset.xyz = offset.xyz * 0.5 + 0.5; // Transform NDC to texture coordinates

        // Get depth of scene at sample's projected screen position
        float sampledSceneDepthViewZ = texture(gPositionView, offset.xy).z;

        // Check if sample is occluded
        // samplePosView.z is view-space Z of the point in the hemisphere
        // sampledSceneDepthViewZ is view-space Z of what's actually in the G-Buffer at that screen pixel
        // If Z is negative into screen (OpenGL standard), samplePosView.z >= sampledSceneDepthViewZ means sample is closer or at same depth
        // This contributes to the original fragPosView being occluded.
        float rangeCheck = smoothstep(0.0, 1.0, radius / abs(fragPosView.z - sampledSceneDepthViewZ));
        if(samplePosView.z >= sampledSceneDepthViewZ + bias)
        {
            occlusion += 1.0 * rangeCheck;
        }
    }

    occlusion = 1.0 - (occlusion / float(kernelSize));
    FragColor = vec4(pow(occlusion, ssaoPower), pow(occlusion, ssaoPower), pow(occlusion, ssaoPower), 1.0);
} 