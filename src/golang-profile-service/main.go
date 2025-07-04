package main

import (
	"net/http"
	"strconv"
	"sync"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

type Profile struct {
	ID       int    `json:"id"`
	Name     string `json:"name"`
	Email    string `json:"email"`
	Age      int    `json:"age"`
	Location string `json:"location"`
}

type ProfileService struct {
	profiles map[int]*Profile
	mutex    sync.RWMutex
	nextID   int
}

func NewProfileService() *ProfileService {
	return &ProfileService{
		profiles: make(map[int]*Profile),
		nextID:   1,
	}
}

func (ps *ProfileService) CreateProfile(profile *Profile) *Profile {
	ps.mutex.Lock()
	defer ps.mutex.Unlock()

	profile.ID = ps.nextID
	ps.profiles[profile.ID] = profile
	ps.nextID++

	return profile
}

func (ps *ProfileService) GetProfile(id int) (*Profile, bool) {
	ps.mutex.RLock()
	defer ps.mutex.RUnlock()

	profile, exists := ps.profiles[id]
	return profile, exists
}

func (ps *ProfileService) GetAllProfiles() []*Profile {
	ps.mutex.RLock()
	defer ps.mutex.RUnlock()

	profiles := make([]*Profile, 0, len(ps.profiles))
	for _, profile := range ps.profiles {
		profiles = append(profiles, profile)
	}
	return profiles
}

func (ps *ProfileService) UpdateProfile(id int, profile *Profile) (*Profile, bool) {
	ps.mutex.Lock()
	defer ps.mutex.Unlock()

	if _, exists := ps.profiles[id]; !exists {
		return nil, false
	}

	profile.ID = id
	ps.profiles[id] = profile
	return profile, true
}

func (ps *ProfileService) DeleteProfile(id int) bool {
	ps.mutex.Lock()
	defer ps.mutex.Unlock()

	if _, exists := ps.profiles[id]; !exists {
		return false
	}

	delete(ps.profiles, id)
	return true
}

func main() {
	profileService := NewProfileService()

	profileService.CreateProfile(&Profile{
		Name:     "Satya",
		Email:    "satya@www.com",
		Age:      30,
		Location: "Hyderabad",
	})
	profileService.CreateProfile(&Profile{
		Name:     "Amz",
		Email:    "amz@www.com",
		Age:      25,
		Location: "San Francisco",
	})

	r := gin.Default()

	config := cors.DefaultConfig()
	config.AllowAllOrigins = true
	config.AllowMethods = []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"}
	config.AllowHeaders = []string{"Origin", "Content-Type", "Accept", "Authorization"}
	r.Use(cors.New(config))

	r.GET("/healthz", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":  "healthy",
			"service": "profile-service",
		})
	})

	r.GET("/profiles", func(c *gin.Context) {
		profiles := profileService.GetAllProfiles()
		c.JSON(http.StatusOK, gin.H{
			"profiles": profiles,
			"count":    len(profiles),
		})
	})

	r.GET("/profiles/:id", func(c *gin.Context) {
		idStr := c.Param("id")
		id, err := strconv.Atoi(idStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid profile ID"})
			return
		}

		profile, exists := profileService.GetProfile(id)
		if !exists {
			c.JSON(http.StatusNotFound, gin.H{"error": "Profile not found"})
			return
		}

		c.JSON(http.StatusOK, profile)
	})

	r.POST("/profiles", func(c *gin.Context) {
		var profile Profile
		if err := c.ShouldBindJSON(&profile); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		createdProfile := profileService.CreateProfile(&profile)
		c.JSON(http.StatusCreated, createdProfile)
	})

	r.PUT("/profiles/:id", func(c *gin.Context) {
		idStr := c.Param("id")
		id, err := strconv.Atoi(idStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid profile ID"})
			return
		}

		var profile Profile
		if err := c.ShouldBindJSON(&profile); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		updatedProfile, exists := profileService.UpdateProfile(id, &profile)
		if !exists {
			c.JSON(http.StatusNotFound, gin.H{"error": "Profile not found"})
			return
		}

		c.JSON(http.StatusOK, updatedProfile)
	})

	r.DELETE("/profiles/:id", func(c *gin.Context) {
		idStr := c.Param("id")
		id, err := strconv.Atoi(idStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid profile ID"})
			return
		}

		success := profileService.DeleteProfile(id)
		if !success {
			c.JSON(http.StatusNotFound, gin.H{"error": "Profile not found"})
			return
		}

		c.JSON(http.StatusOK, gin.H{"message": "Profile deleted successfully"})
	})

	r.Run(":8080")
}
