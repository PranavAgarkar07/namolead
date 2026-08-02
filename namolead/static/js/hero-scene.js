const canvas = document.querySelector(".hero-scene");
if (!canvas) throw new Error("no canvas"); // browser will swallow since defer
const isWebGL =
  !!window.WebGL2RenderingContext || (() => {
    try { const c = document.createElement("canvas"); return !!(c.getContext("webgl") || c.getContext("experimental-webgl")); }
    catch (_) { return false; }
  })();

if (isWebGL) {
  import("https://cdn.jsdelivr.net/npm/three@0.164.1/build/three.module.js")
    .then((THREE) => {
      const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

      const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setClearColor(0x000000, 0);

      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
      camera.position.set(0, 0, 14);

      scene.add(new THREE.HemisphereLight(0xffffff, 0x102a43, 1.2));
      const key = new THREE.DirectionalLight(0xffffff, 1.5);
      key.position.set(4, 6, 8);
      scene.add(key);

      const colors = [0xfdf9f3, 0xfffaee, 0xff6b35, 0xffffff, 0xfdf9f3, 0xfdf9f3];
      const planes = [];

      function makePaperPlane() {
        const geo = new THREE.BufferGeometry();
        // Nose-up orientation: crease line runs vertically (the center fold),
        // wings spread in X, tail sits lower behind the folded spine.
        const nose = new THREE.Vector3(0, 2.6, 0);        // sharp nose tip
        const spine = new THREE.Vector3(0, -0.35, 0.15); // center crease root (ridge)
        const tipL = new THREE.Vector3(-1.45, -0.1, 0.4);  // swept left wing tip
        const tipR = new THREE.Vector3(1.45, -0.1, 0.4);   // swept right wing tip
        const tailL = new THREE.Vector3(-0.5, -0.7, -0.55); // left tail point (keel)
        const tailR = new THREE.Vector3(0.5, -0.7, -0.55);  // right tail point (keel)

        const pos = [];
        function push(v) { pos.push(v.x, v.y, v.z); }

        // upper fold (top sheet, one smooth plane from nose to the spread wings)
        push(nose); push(spine); push(tipL);
        push(nose); push(tipR); push(spine);
        // lower V (the folded underside of each wing down to the tail keel)
        push(spine); push(tipL); push(tailL);
        push(spine); push(tailR); push(tipR);

        geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
        geo.computeVertexNormals();
        const color = colors[Math.floor(Math.random() * colors.length)];
        const mat = new THREE.MeshStandardMaterial({
          color,
          roughness: 0.6,
          metalness: 0,
          flatShading: true,
          side: THREE.DoubleSide,
        });
        return new THREE.Mesh(geo, mat);
      }

      function spawn() {
        const mesh = makePaperPlane();
        const s = 0.6 + Math.random() * 1.1;
        const x = (Math.random() * 2 - 1) * 6;
        mesh.scale.setScalar(s);
        mesh.rotation.x = (Math.random() * 2 - 1) * 0.2; // gentle tilt toward viewer
        mesh.position.set(x, -6 - Math.random() * 4, Math.random() * -6);
        planes.push({
          mesh,
          baseX: x,
          speed: 0.6 + Math.random() * 0.9,
          flutter: (Math.random() * 2 - 1) * 0.35, // slow wing rock
          sway: 0.4 + Math.random() * 0.8,          // lateral glide amplitude
          phase: Math.random() * Math.PI * 2,
        });
        scene.add(mesh);
      }

      for (let i = 0; i < 16; i++) spawn();

      const mouse = { x: 0, y: 0 };
      canvas.addEventListener("pointermove", (e) => {
        mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
        mouse.y = (e.clientY / window.innerHeight) * 2 - 1;
      });

      function resize() {
        const rect = canvas.getBoundingClientRect();
        if (!rect.width || !rect.height) return;
        renderer.setSize(rect.width, rect.height, false);
        camera.aspect = rect.width / rect.height;
        camera.updateProjectionMatrix();
      }
      resize();
      window.addEventListener("resize", resize);

      const clock = new THREE.Clock();
      function frame() {
        const dt = Math.min(clock.getDelta(), 0.05);
        camera.position.x = THREE.MathUtils.lerp(camera.position.x, mouse.x * 2, 0.05);
        camera.position.y = THREE.MathUtils.lerp(camera.position.y, mouse.y * 1.2, 0.05);
        camera.lookAt(0, 0, 0);

        for (const p of planes) {
          const t = clock.elapsedTime;
          // glide upward, drifting sideways along a gentle sine path
          p.mesh.position.y += p.speed * dt;
          p.mesh.position.x = p.baseX + Math.sin(t * 0.4 + p.phase) * p.sway;
          // bank: constant cruise + slow rock, no flipping/spinning
          p.mesh.rotation.z = 0.12 + Math.sin(t * 0.35 + p.phase * 2) * p.flutter;
          p.mesh.rotation.y = Math.sin(t * 0.25 + p.phase) * 0.18;
          if (p.mesh.position.y > 9) {
            p.mesh.position.y = -7;
            p.baseX = (Math.random() * 2 - 1) * 9;
            p.phase = Math.random() * Math.PI * 2;
          }
        }
        renderer.render(scene, camera);
      }

      function loop() {
        if (reduced) return;
        requestAnimationFrame(loop);
        frame();
      }
      if (reduced) {
        renderer.render(scene, camera);
      } else {
        loop();
      }
    })
    .catch(() => {});
}