const canvas = document.querySelector(".hero-scene");
const isWebGL =
  !!window.WebGL2RenderingContext ||
  (() => {
    try {
      const c = document.createElement("canvas");
      return !!(c.getContext("webgl") || c.getContext("experimental-webgl"));
    } catch (_) {
      return false;
    }
  })();

if (canvas && isWebGL) {
  import("https://cdn.jsdelivr.net/npm/three@0.164.1/build/three.module.js")
    .then((THREE) => {
      const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

      const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setClearColor(0x000000, 0);

      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
      camera.position.set(0, 0, 14);

      scene.add(new THREE.HemisphereLight(0xdce7ff, 0x102a43, 1.15));
      const key = new THREE.DirectionalLight(0xffffff, 1.4);
      key.position.set(-3, 6, 7);
      scene.add(key);
      const rim = new THREE.DirectionalLight(0xff6b35, 0.35);
      rim.position.set(4, -2, -6);
      scene.add(rim);

      const PAPER = 0xfdf9f3;
      const CREAM = 0xfff8ec;
      const ORANGE = 0xff6b35;
      const NAVY = 0x102a43;
      const CLOUD = 0xfffdf4;

      // ---------------------------------------------------------------
      // Crowd: paper-cut silhouettes on a ground strip (InstancedMesh)
      // ---------------------------------------------------------------
      function makePersonGeo() {
        const g = new THREE.BufferGeometry();
        // silhouettes: ovoid head over a soft capsule torso, flat-backed
        const head = new THREE.SphereGeometry(0.15, 10, 8);
        head.translate(0, 1.06, 0);
        const torso = new THREE.CylinderGeometry(0.16, 0.22, 1.05, 8);
        torso.translate(0, 0.45, 0);
        const base = new THREE.BoxGeometry(0.15, 0.04, 0.44);
        base.translate(0, 0.0, 0);
        const pos = [];
        for (const p of [head, torso, base]) {
          const a = p.attributes.position.array;
          for (let i = 0; i < a.length; i += 3) pos.push(a[i], a[i + 1], a[i + 2]);
        }
        g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
        g.computeVertexNormals();
        return g;
      }

      const crowdMaterial = new THREE.MeshStandardMaterial({
        color: CREAM,
        roughness: 0.7,
        metalness: 0,
        flatShading: true,
        side: THREE.DoubleSide,
      });

      const CROWD_COUNT = 42;
      const people = new THREE.InstancedMesh(makePersonGeo(), crowdMaterial, CROWD_COUNT);
      const dummy = new THREE.Object3D();
      const ground = -4.55;
      const crowd = [];
      for (let i = 0; i < CROWD_COUNT; i++) {
        const x = (i / (CROWD_COUNT - 1) - 0.5) * 30;
        const s = 0.8 + Math.random() * 0.45;
        const z = Math.random() * -2 - 1;
        dummy.position.set(x, ground, z);
        dummy.rotation.set(0, (Math.random() * 2 - 1) * 0.18, 0);
        dummy.scale.set(s, s, s);
        dummy.updateMatrix();
        people.setMatrixAt(i, dummy.matrix);
        crowd.push({ x, z, scale: s, phase: Math.random() * Math.PI * 2 });
      }
      people.instanceMatrix.needsUpdate = true;
      scene.add(people);

      // ground strip shadow for grounding
      const strip = new THREE.Mesh(
        new THREE.BoxGeometry(32, 0.06, 7),
        new THREE.MeshStandardMaterial({ color: 0x0b2237, roughness: 1, flatShading: true })
      );
      strip.position.y = ground - 0.03;
      scene.add(strip);

      // ---------------------------------------------------------------
      // Clouds: low-poly paper tufts (jittered merged spheres, flat base)
      // ---------------------------------------------------------------
      const cloudMat = new THREE.MeshStandardMaterial({
        color: CLOUD,
        roughness: 0.85,
        metalness: 0,
        flatShading: true,
      });

      function makeCloud(scale) {
        const group = new THREE.Group();
        const parts = [
          [0, 0, 0, 1.0],
          [-0.85, -0.12, 0.25, 0.72],
          [0.85, -0.12, -0.25, 0.74],
          [0.4, 0.18, 0.3, 0.6],
        ];
        for (const [x, y, z, s] of parts) {
          const sph = new THREE.Mesh(new THREE.SphereGeometry(s * scale * 0.6, 8, 7), cloudMat);
          sph.position.set(x * scale * 0.6, y * scale * 0.6, (z + (Math.random() - 0.5) * 0.3) * scale * 0.6);
          sph.scale.y = 0.72; // squash to a fat flat-bottomed tuft
          group.add(sph);
        }
        return group;
      }

      const clouds = [];
      for (let i = 0; i < 12; i++) {
        const layer = i < 5 ? 2.5 : 1.2; // far vs near parallax depth
        const cl = makeCloud(2 + Math.random() * 2, layer);
        cl.position.set((Math.random() * 2 - 1) * 22, i < 5 ? 4 + Math.random() * 3 : 1.2 + Math.random() * 2.2, -4 - Math.random() * 4);
        cl.rotation.y = Math.random() * 0.5 - 0.25;
        scene.add(cl);
        clouds.push({ mesh: cl, layer, speed: 0.35 * layer, baseY: cl.position.y });
      }

      // ---------------------------------------------------------------
      // The riser: one person above the cloud line
      // ---------------------------------------------------------------
      const riseMat = new THREE.MeshStandardMaterial({
        color: ORANGE,
        roughness: 0.6,
        metalness: 0,
        flatShading: true,
        side: THREE.DoubleSide,
      });
      const riser = new THREE.Mesh(makePersonGeo(), riseMat);
      riser.scale.setScalar(1.25);
      riser.position.set(-3.6, 4.6, 1.5);
      riser.rotation.z = -0.08;
      scene.add(riser);

      // ---------------------------------------------------------------
      // Ascent trail: small paper planes rising behind the riser
      // ---------------------------------------------------------------
      function makePaperPlane() {
        const geo = new THREE.BufferGeometry();
        const nose = new THREE.Vector3(0, 2.6, 0);
        const spine = new THREE.Vector3(0, -0.35, 0.15);
        const tipL = new THREE.Vector3(-1.45, -0.1, 0.4);
        const tipR = new THREE.Vector3(1.45, -0.1, 0.4);
        const tailL = new THREE.Vector3(-0.5, -0.7, -0.55);
        const tailR = new THREE.Vector3(0.5, -0.7, -0.55);
        const pos = [];
        const push = (v) => pos.push(v.x, v.y, v.z);
        push(nose); push(spine); push(tipL);
        push(nose); push(tipR); push(spine);
        push(spine); push(tipL); push(tailL);
        push(spine); push(tailR); push(tipR);
        geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
        geo.computeVertexNormals();
        const mat = new THREE.MeshStandardMaterial({
          color: Math.random() > 0.5 ? PAPER : ORANGE,
          roughness: 0.6,
          flatShading: true,
          side: THREE.DoubleSide,
          transparent: true,
          opacity: 0.85,
        });
        return new THREE.Mesh(geo, mat);
      }

      const trail = [];
      for (let i = 0; i < 14; i++) {
        const m = makePaperPlane();
        m.scale.setScalar(0.16 + Math.random() * 0.1);
        m.position.set(riser.position.x - i * 0.9 + (Math.random() - 0.5) * 0.7, riser.position.y - i * 0.72 - 0.4, riser.z + 0.3);
        scene.add(m);
        trail.push({ mesh: m, phase: Math.random() * Math.PI * 2 });
      }

      // ---------------------------------------------------------------
      // Interaction + animation
      // ---------------------------------------------------------------
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
        const t = clock.elapsedTime;
        if (!reduced) {
          camera.position.x = THREE.MathUtils.lerp(camera.position.x, mouse.x * 1.6, 0.04);
          camera.position.y = THREE.MathUtils.lerp(camera.position.y, mouse.y * 0.9, 0.04);
          camera.lookAt(0, 0, 0);
        }

        // crowd: gentle "pay attention" bob
        for (let i = 0; i < CROWD_COUNT; i++) {
          const c = crowd[i];
          dummy.position.set(c.x, ground + Math.sin(t * 0.8 + c.phase) * 0.045, c.z);
          dummy.scale.set(c.scale, c.scale * (1 + Math.sin(t * 0.9 + c.phase) * 0.02), c.scale);
          dummy.updateMatrix();
          people.setMatrixAt(i, dummy.matrix);
        }
        people.instanceMatrix.needsUpdate = true;

        // clouds parallax
        for (const c of clouds) {
          c.mesh.position.x += c.speed * dt;
          if (c.mesh.position.x > 24) c.mesh.position.x = -24;
        }

        // riser hover + trail rise
        riser.position.y = 4.6 + Math.sin(t * 0.7) * 0.25;
        riser.rotation.z = -0.08 + Math.sin(t * 1.1) * 0.05;
        for (let i = 0; i < trail.length; i++) {
          const tl = trail[i];
          tl.mesh.position.y += (0.25 + i * 0.008) * dt;
          tl.mesh.rotation.z = Math.sin(t * 0.8 + tl.phase) * 0.15;
          tl.mesh.rotation.y = Math.sin(t * 0.9 + tl.phase) * 0.2;
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