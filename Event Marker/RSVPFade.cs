using System.Collections;
using System.Collections.Generic;
using Valve.VR.InteractionSystem;
using UnityEngine;
using System;

public class RSVPFade : MonoBehaviour
{
    private float timeElapsed;
    public float fadeawayTime;
    public bool isShowing = false;

    private float distFromPlayer;

    public SessionParam sessionScript;
    public ItemManagerScript itemManager;

    double itemID;
    double itemDTNType;
    void Start()
    {
    }

    // Update is called once per frame
    void Update()
    {
    }

    public void PrepareToShow(float dist, float ftime)
    {
        fadeawayTime = ftime;
        distFromPlayer = dist;
        gameObject.transform.position = Camera.main.transform.position + distFromPlayer * Vector3.forward;
        isShowing = true;
        gameObject.SetActive(true);

        itemID = itemManager.GetItemCatalogValue(gameObject);
        itemDTNType = itemManager.GetItemDTNType(itemID);
        sessionScript.InsertEventMarkers(new List<string>() { "DTN", "itemID", "objDistFromPlayer" }, new List<double>() { itemDTNType, itemID, distFromPlayer });
        
        StartCoroutine(fadeAwayCoroutine());
    }

    private IEnumerator fadeAwayCoroutine()
    {
        yield return new WaitForSeconds(fadeawayTime);
        isShowing = false;
        sessionScript.InsertEventMarkers(new List<string>() { "DTN", "itemID" }, new List<double>() { -itemDTNType, -itemID});
        gameObject.SetActive(false);
        Destroy(gameObject);
    }


}
